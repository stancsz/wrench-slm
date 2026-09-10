import json

import pytest
import torch
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace
from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM

from wrench.dataset import JsonlDataset, collate_sft, format_completion
from wrench.protocol import prediction_matches_target
from wrench.sft import sft_train


@pytest.fixture
def tokenizer():
    backend = Tokenizer(WordLevel({'[UNK]': 0, '[PAD]': 1, '[EOS]': 2, 'status': 3}, unk_token='[UNK]'))
    backend.pre_tokenizer = Whitespace()
    return PreTrainedTokenizerFast(tokenizer_object=backend, unk_token='[UNK]', pad_token='[PAD]', eos_token='[EOS]')


@pytest.fixture
def records(tmp_path):
    path = tmp_path / 'train.jsonl'
    path.write_text('\n'.join(json.dumps({'id': str(i), 'prompt': 'status ' * (i + 1), 'tool': 'get_goal', 'args': {}}) for i in range(3)), encoding='utf-8')
    return path


def model():
    torch.manual_seed(5)
    return Qwen2ForCausalLM(Qwen2Config(vocab_size=4, hidden_size=16, intermediate_size=32, num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=2))


def test_complete_targets_masking_and_padding(tokenizer, records):
    samples = list(JsonlDataset(records, tokenizer))
    batch = collate_sft(samples, tokenizer.pad_token_id)
    assert batch['input_ids'].shape[0] == 3
    for i, sample in enumerate(samples):
        assert sample['labels'][-1] == tokenizer.eos_token_id
        assert sample['labels'][0] == -100
        length = len(sample['input_ids'])
        assert (batch['labels'][i, length:] == -100).all()
        assert (batch['attention_mask'][i, length:] == 0).all()
    assert torch.isfinite(model()(**batch).loss)


def test_oversize_is_rejected_not_truncated(tokenizer, records):
    with pytest.raises(ValueError, match='truncation is forbidden'):
        list(JsonlDataset(records, tokenizer, max_length=8))


def test_fallback_and_all_arguments_are_scored():
    assert format_completion({'tool': 'fallback'}) == 'ROUTER_FALLBACK'
    assert prediction_matches_target('ROUTER_FALLBACK', {'tool': 'fallback'})
    assert not prediction_matches_target('{"tool":"fallback","args":{}}', {'tool': 'fallback'})
    record = {'tool': 'update_goal', 'args': {'status': 'complete'}}
    assert not prediction_matches_target('{"tool":"update_goal","args":{"status":"blocked"}}', record)
    assert prediction_matches_target('{"args":{"status":"complete"},"tool":"update_goal"}', record)
    assert not prediction_matches_target('invalid', record)


def test_sft_learns_reloads_and_resumes(tokenizer, records, tmp_path):
    torch.set_num_threads(1)
    kwargs = dict(micro_batch_size=2, grad_accum_steps=2, learning_rate=0.01, log_every=20)
    uninterrupted = model()
    full = sft_train(uninterrupted, tokenizer, str(records), max_steps=8, **kwargs)
    assert full.loss_end < full.loss_start
    first = model()
    save_dir = tmp_path / 'candidate'
    initial = sft_train(first, tokenizer, str(records), max_steps=3, checkpoint_dir=save_dir, **kwargs)
    loaded = Qwen2ForCausalLM.from_pretrained(save_dir)
    loaded_tokenizer = PreTrainedTokenizerFast.from_pretrained(save_dir)
    assert loaded_tokenizer.get_vocab() == tokenizer.get_vocab()
    resumed = sft_train(loaded, loaded_tokenizer, str(records), max_steps=8, resume_from=save_dir / 'trainer_state.pt', **kwargs)
    assert resumed.examples_seen == full.examples_seen > initial.examples_seen
    for name, tensor in uninterrupted.state_dict().items():
        torch.testing.assert_close(loaded.state_dict()[name], tensor, rtol=0, atol=0)
    changed = tmp_path / 'changed.jsonl'
    changed.write_text(records.read_text() + '\n{}', encoding='utf-8')
    with pytest.raises(ValueError, match='contract mismatch'):
        sft_train(model(), tokenizer, str(changed), resume_from=save_dir / 'trainer_state.pt', **kwargs)


def test_validation_and_empty_dataset(tokenizer, records, tmp_path):
    result = sft_train(model(), tokenizer, str(records), val_path=str(records), max_steps=1, grad_accum_steps=1)
    assert result.validation_loss is not None
    empty = tmp_path / 'empty.jsonl'
    empty.write_text('', encoding='utf-8')
    with pytest.raises(ValueError, match='empty'):
        sft_train(model(), tokenizer, str(empty), max_steps=1)


def test_periodic_checkpoint_resumes_exactly(tokenizer, records, tmp_path):
    torch.set_num_threads(1)
    kwargs = dict(micro_batch_size=2, grad_accum_steps=2, learning_rate=0.01, val_path=str(records))
    full = model()
    sft_train(full, tokenizer, str(records), max_steps=4,
              checkpoint_dir=tmp_path / 'full' / 'checkpoint', checkpoint_every=2, **kwargs)
    intermediate = tmp_path / 'full' / 'step-000002'
    assert json.loads((intermediate / 'training_metrics.json').read_text())['validation_loss'] > 0
    loaded = Qwen2ForCausalLM.from_pretrained(intermediate)
    sft_train(loaded, tokenizer, str(records), max_steps=4,
              resume_from=intermediate / 'trainer_state.pt', **kwargs)
    for name, tensor in full.state_dict().items():
        torch.testing.assert_close(loaded.state_dict()[name], tensor, rtol=0, atol=0)


def test_lora_checkpoint_resume_preserves_training(tokenizer, records, tmp_path):
    from peft import LoraConfig, get_peft_model

    def lora():
        return get_peft_model(model(), LoraConfig(r=2, lora_alpha=4, lora_dropout=.05,
                                                 target_modules=['q_proj', 'v_proj'], task_type='CAUSAL_LM'))

    torch.set_num_threads(1)
    kwargs = dict(micro_batch_size=2, grad_accum_steps=2, learning_rate=.01)
    full = lora()
    sft_train(full, tokenizer, str(records), max_steps=4, checkpoint_every=2,
              checkpoint_dir=tmp_path / 'full' / 'checkpoint', **kwargs)
    restored = lora()
    sft_train(restored, tokenizer, str(records), max_steps=4,
              resume_from=tmp_path / 'full' / 'step-000002' / 'trainer_state.pt', **kwargs)
    for name, tensor in full.state_dict().items():
        torch.testing.assert_close(restored.state_dict()[name], tensor, rtol=0, atol=0)

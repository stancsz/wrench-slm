"""Bounded, resumable SFT for isolated pretrained-model candidates."""

from dataclasses import asdict, dataclass
from functools import partial
import hashlib
import json
from pathlib import Path
import time

import torch
from torch.utils.data import DataLoader

from .dataset import JsonlDataset, collate_sft


@dataclass
class TrainingMetrics:
    steps: int
    loss_start: float
    loss_end: float
    duration_s: float
    examples_seen: int
    validation_loss: float | None = None


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _loader(path, tokenizer, max_length, batch_size, seed):
    pad = tokenizer.pad_token_id
    if pad is None:
        pad = tokenizer.eos_token_id
    return DataLoader(
        JsonlDataset(path, tokenizer, max_length=max_length), batch_size=batch_size,
        collate_fn=partial(collate_sft, pad_token_id=pad), num_workers=0,
        generator=torch.Generator().manual_seed(seed),
    )


def _next(iterator, loader):
    try:
        return next(iterator), iterator
    except StopIteration:
        iterator = iter(loader)
        try:
            return next(iterator), iterator
        except StopIteration as exc:
            raise ValueError('Training dataset is empty') from exc


@torch.no_grad()
def validation_loss(model, loader):
    was_training = model.training
    model.eval()
    total = count = 0
    try:
        for batch in loader:
            batch = {k: v.to(model.device) for k, v in batch.items()}
            tokens = int((batch['labels'][:, 1:] != -100).sum())
            loss = model(**batch).loss
            if not torch.isfinite(loss):
                raise ValueError('Non-finite validation loss')
            total += float(loss) * tokens
            count += tokens
    finally:
        model.train(was_training)
    if not count:
        raise ValueError('Validation dataset has no supervised tokens')
    return total / count


def sft_train(
    model, tokenizer, train_path: str, *, val_path=None, micro_batch_size=1,
    grad_accum_steps=16, learning_rate=1e-4, max_steps=500, log_every=25,
    seed=42, max_length=1024, checkpoint_dir=None, resume_from=None,
    checkpoint_every=None,
):
    """max_steps is the total optimizer-step target, including resumed steps.

    Constant learning rate; deterministic sequential data with cyclic replay.
    Checkpoints include model/optimizer/RNG states and an exact input contract.
    Only load checkpoints produced by this local training pipeline.
    """
    if min(micro_batch_size, grad_accum_steps, max_steps, log_every) < 1:
        raise ValueError('Batch, accumulation, steps and logging interval must be positive')
    if max_length < 2 or learning_rate <= 0:
        raise ValueError('Invalid sequence length or learning rate')
    if checkpoint_every is not None and (checkpoint_every < 1 or checkpoint_dir is None):
        raise ValueError('Periodic checkpoints require a directory and positive interval')
    torch.manual_seed(seed)
    contract = {
        'formatter_sha256': _digest(Path(__file__).with_name('dataset.py')),
        'train_sha256': _digest(train_path), 'val_sha256': _digest(val_path) if val_path else None,
        'vocab_sha256': hashlib.sha256(json.dumps(tokenizer.get_vocab(), sort_keys=True).encode()).hexdigest(),
        'chat_template': getattr(tokenizer, 'chat_template', None),
        'special_tokens': tokenizer.special_tokens_map,
        'micro_batch_size': micro_batch_size, 'grad_accum_steps': grad_accum_steps,
        'learning_rate': learning_rate, 'schedule': 'constant', 'seed': seed,
        'max_length': max_length,
    }
    loader = _loader(train_path, tokenizer, max_length, micro_batch_size, seed)
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=learning_rate,
    )
    start_step = examples = batches_seen = 0
    loss_start = loss_end = 0.0
    checkpoint = None
    if resume_from:
        checkpoint = torch.load(resume_from, map_location='cpu', weights_only=False)
        if checkpoint['contract'] != contract:
            raise ValueError('Checkpoint dataset/tokenizer/training contract mismatch')
        model.load_state_dict(checkpoint['model'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        start_step = checkpoint['step']
        examples = checkpoint['examples_seen']
        batches_seen = checkpoint['batches_seen']
        loss_start, loss_end = checkpoint['loss_start'], checkpoint['loss_end']
        if start_step > max_steps:
            raise ValueError('Checkpoint is beyond requested max_steps')
    iterator = iter(loader)
    for _ in range(batches_seen):
        _, iterator = _next(iterator, loader)
    if checkpoint:
        torch.set_rng_state(checkpoint['rng_cpu'])
        if torch.cuda.is_available() and checkpoint['rng_cuda'] is not None:
            torch.cuda.set_rng_state_all(checkpoint['rng_cuda'])
    model.train()
    started = time.perf_counter()

    def save_checkpoint(path, completed_steps, val):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        metrics = TrainingMetrics(completed_steps, loss_start, loss_end, time.perf_counter() - started, examples, val)
        payload = {
            'contract': contract, 'model': model.state_dict(), 'optimizer': optimizer.state_dict(),
            'step': completed_steps, 'examples_seen': examples, 'batches_seen': batches_seen,
            'loss_start': loss_start, 'loss_end': loss_end,
            'rng_cpu': torch.get_rng_state(),
            'rng_cuda': torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        }
        temporary = path / 'trainer_state.tmp'
        torch.save(payload, temporary)
        temporary.replace(path / 'trainer_state.pt')
        model.save_pretrained(path)
        tokenizer.save_pretrained(path)
        (path / 'training_metrics.json').write_text(json.dumps(asdict(metrics), indent=2), encoding='utf-8')
        (path / 'training_contract.json').write_text(json.dumps(contract, indent=2), encoding='utf-8')

    for step in range(start_step, max_steps):
        optimizer.zero_grad(set_to_none=True)
        accumulated = 0.0
        for _ in range(grad_accum_steps):
            batch, iterator = _next(iterator, loader)
            batch = {k: v.to(model.device) for k, v in batch.items()}
            loss = model(**batch).loss / grad_accum_steps
            if not torch.isfinite(loss):
                raise ValueError(f'Non-finite training loss at step {step}')
            loss.backward()
            accumulated += float(loss.detach())
            examples += batch['input_ids'].shape[0]
            batches_seen += 1
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
        optimizer.step()
        loss_end = accumulated
        if step == 0:
            loss_start = accumulated
        if (step + 1) % log_every == 0 or step + 1 == max_steps:
            print(f'[sft] step {step + 1}/{max_steps} loss={accumulated:.6f}', flush=True)
            if checkpoint_dir:
                history_path = Path(checkpoint_dir).parent / 'training_history.jsonl'
                history_path.parent.mkdir(parents=True, exist_ok=True)
                with history_path.open('a', encoding='utf-8') as history:
                    history.write(json.dumps({'step': step + 1, 'loss': accumulated,
                                              'examples_seen': examples, 'elapsed_s': time.perf_counter() - started}) + '\n')
        if checkpoint_every and (step + 1) % checkpoint_every == 0 and step + 1 < max_steps:
            val = validation_loss(model, _loader(val_path, tokenizer, max_length, micro_batch_size, seed)) if val_path else None
            save_checkpoint(Path(checkpoint_dir).parent / f'step-{step + 1:06d}', step + 1, val)
            print(f'[sft] checkpoint step={step + 1} validation_loss={val}', flush=True)
    val = validation_loss(model, _loader(val_path, tokenizer, max_length, micro_batch_size, seed)) if val_path else None
    metrics = TrainingMetrics(max_steps, loss_start, loss_end, time.perf_counter() - started, examples, val)
    if checkpoint_dir:
        save_checkpoint(checkpoint_dir, max_steps, val)
    return metrics

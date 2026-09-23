const chinese = document.documentElement.lang === 'zh-CN';
document.querySelectorAll('.language-switch').forEach(link => {
  if (window.location.hash) link.hash = window.location.hash;
  link.addEventListener('click', () => { link.hash = window.location.hash; });
});
document.querySelectorAll('[data-copy]').forEach(button => {
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(button.parentElement.querySelector('code').textContent);
      button.textContent = chinese ? '复制好了' : 'Copied';
    } catch {
      button.textContent = chinese ? '请选中代码手动复制' : 'Select code to copy';
    }
  });
});

const controls = document.querySelectorAll('[data-case]');
if (controls.length) {
  fetch(chinese ? '../assets/demo-receipt.json' : 'assets/demo-receipt.json').then(response => {
    if (!response.ok) throw new Error('Receipt unavailable');
    return response.json();
  }).then(receipt => {
    controls.forEach(button => {
      button.disabled = false;
      button.addEventListener('click', () => {
        controls.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
        const item = receipt.cases[Number(button.dataset.case)];
        document.querySelector('#demo-output').textContent = JSON.stringify(item.result, null, 2);
        document.querySelector('#demo-title').textContent = button.dataset.title || item.title;
      });
    });
  }).catch(() => {
    document.querySelector('#demo-title').textContent = chinese ? '暂时没读到保存的结果。下面的例子仍然可以查看。' : 'Saved receipt unavailable. The example below remains readable.';
  });
}

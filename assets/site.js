/* The generated catalog is the only list of visualizations the shell needs. */
(() => {
  'use strict';
  const site = window.STAT250_SITE;
  if (!site) return;
  const entries = site.visualizations;
  const tabs = document.querySelector('#tabs');
  const selector = document.querySelector('#visualization-select');
  const panels = document.querySelector('#visualization-panels');
  const allIds = ['overview', ...entries.map(entry => entry.id)];
  const mounted = new Map();
  document.querySelector('.skip-link').addEventListener('click', event => {
    event.preventDefault();
    const main = document.querySelector('#main');
    main.focus();
    main.scrollIntoView({block: 'start'});
  });

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  for (const [attribute, value] of [['title', site.title], ['subtitle', site.subtitle], ['term', site.term]]) {
    document.querySelectorAll(`[data-site-${attribute}]`).forEach(node => { node.textContent = value; });
  }
  const credit = document.querySelector('#site-authorship');
  for (const [label, value, url] of [
    ['Ideas and instructional design', site.authorship.ideas, site.authorship.ideas_url],
    ['Implementation', site.authorship.implementation]
  ]) {
    const span = element('span', '', `${label}: `);
    const name = element('strong', '', value);
    if (url) {
      const link = element('a');
      link.href = url;
      link.append(name);
      span.append(link);
    } else {
      span.append(name);
    }
    credit.append(span);
  }

  for (const item of [{id: 'overview', title: 'How to use'}, ...entries]) {
    const button = element('button', 'tab', item.title);
    button.id = `tab-${item.id}`;
    button.type = 'button';
    button.setAttribute('role', 'tab');
    button.setAttribute('aria-controls', `panel-${item.id}`);
    button.addEventListener('click', () => { window.location.hash = item.id; });
    tabs.append(button);
    const option = element('option', '', item.title);
    option.value = item.id;
    selector.append(option);
    if (item.id !== 'overview') {
      const panel = element('section', 'visualization-panel');
      panel.id = `panel-${item.id}`;
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', `tab-${item.id}`);
      panel.tabIndex = 0;
      panel.hidden = true;
      panels.append(panel);
    }
  }
  selector.addEventListener('change', () => { window.location.hash = selector.value; });
  tabs.addEventListener('keydown', event => {
    const index = [...tabs.children].indexOf(event.target);
    if (index < 0) return;
    let next;
    if (event.key === 'ArrowRight') next = (index + 1) % allIds.length;
    else if (event.key === 'ArrowLeft') next = (index + allIds.length - 1) % allIds.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = allIds.length - 1;
    else return;
    event.preventDefault();
    tabs.children[next].focus();
    window.location.hash = allIds[next];
  });

  const teaching = entries.filter(entry => entry.kind !== 'preview');
  const previews = entries.filter(entry => entry.kind === 'preview');
  document.querySelector('#collection-count').textContent = `${teaching.length} teaching visualization${teaching.length === 1 ? '' : 's'}${previews.length ? ` · ${previews.length} preview${previews.length === 1 ? '' : 's'}` : ''}`;
  const grid = document.querySelector('#collection-grid');
  if (!teaching.length) {
    grid.append(element('p', 'empty-state', 'No course visualizations have been added yet.'));
  }
  for (const entry of entries) {
    const card = element('article', 'collection-entry');
    const title = element('h3');
    const link = element('a', '', entry.title);
    link.href = `#${entry.id}`;
    title.append(link);
    card.append(title, element('p', '', entry.description));
    grid.append(card);
  }

  function mount(entry) {
    const panel = document.querySelector(`#panel-${entry.id}`);
    const toolbar = element('div', 'visualization-toolbar');
    const breadcrumb = element('p', 'visualization-breadcrumb', 'Collection / ');
    breadcrumb.append(element('span', '', entry.title));
    const actions = element('div', 'visualization-actions');
    const open = element('a', 'button button-secondary', 'Open on its own ↗');
    open.href = entry.file;
    open.target = '_blank';
    open.rel = 'noopener';
    open.setAttribute('aria-label', `Open ${entry.title} on its own in a new tab`);
    const download = element('a', 'button');
    download.innerHTML = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3v9m-3-3 3 3 3-3M4 13v3h12v-3"/></svg>';
    download.append(document.createTextNode('Download'));
    download.href = entry.file;
    download.download = `stat250-${entry.id}.html`;
    download.setAttribute('aria-label', `Download ${entry.title} as a standalone HTML file`);
    actions.append(open, download);
    toolbar.append(breadcrumb, actions);
    const frame = element('iframe', 'visualization-frame');
    frame.title = entry.title;
    frame.src = entry.file;
    frame.addEventListener('load', () => {
      // The files are hosted together, so measure the actual content rather than
      // requiring individual visualizations to implement a messaging protocol.
      const body = frame.contentDocument?.body;
      if (!body) return;
      const resize = () => {
        if (panel.hidden) return;
        frame.style.height = `${Math.ceil(body.getBoundingClientRect().height) + 2}px`;
      };
      const observer = new ResizeObserver(resize);
      observer.observe(body);
      mounted.get(entry.id).resize = resize;
      resize();
    });
    panel.append(toolbar, frame, element('p', 'download-note', 'Download the HTML file to use or edit it offline.'));
    mounted.set(entry.id, {panel, frame});
    return panel;
  }

  function route() {
    let id;
    try { id = decodeURIComponent(window.location.hash.slice(1)) || 'overview'; }
    catch { id = ''; }
    const unknown = !allIds.includes(id);
    if (unknown) id = 'overview';
    const notice = document.querySelector('#route-message');
    notice.hidden = !unknown;
    notice.textContent = unknown ? 'That visualization is not in the collection. Choose one below.' : '';
    const entry = entries.find(item => item.id === id);
    if (entry && !mounted.has(id)) mount(entry);
    document.querySelector('#panel-overview').hidden = id !== 'overview';
    for (const [key, value] of mounted) {
      value.panel.hidden = key !== id;
      if (key === id && value.resize) requestAnimationFrame(value.resize);
    }
    for (const button of tabs.children) {
      const selected = button.id === `tab-${id}`;
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
    }
    selector.value = id;
    document.title = entry ? `${entry.title} · ${site.title}` : `${site.title} · ${site.subtitle}`;
  }
  window.addEventListener('hashchange', route);
  route();

})();

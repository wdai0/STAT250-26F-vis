/* The generated catalog is the only list of visualizations the shell needs. */
(() => {
  'use strict';
  const site = window.STAT250_SITE;
  if (!site) return;
  const entries = site.visualizations;
  const browseButton = document.querySelector('#browse-button');
  const dialog = document.querySelector('#browse-dialog');
  const search = document.querySelector('#visualization-search');
  const clearSearch = document.querySelector('#clear-search');
  const results = document.querySelector('#browse-results');
  const homeId = site.homepage || entries[0]?.id;
  const guideId = 'create-your-own';
  const guideLink = document.querySelector('#create-link');
  const homeLink = document.querySelector('#home-link');
  const papersLink = document.querySelector('#papers-link');
  let activeId = homeId;
  let focusOnRoute = false;
  const panels = document.querySelector('#visualization-panels');
  const allIds = entries.map(entry => entry.id);
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

  function formatPValues(node) {
    const parts = node.textContent.split(/\b(p)(?=-values?\b)/g);
    node.replaceChildren(...parts.map((part, index) => index % 2
      ? element('var', 'stat-symbol', part) : document.createTextNode(part)));
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

  function navigate(event, id) {
    // Preserve opening a direct link in another tab with modifier keys.
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (dialog.open) dialog.close();
    focusOnRoute = true;
    if (window.location.hash === `#${id}`) route();
    else window.location.hash = id;
  }
  guideLink.addEventListener('click', event => navigate(event, guideId));
  homeLink.addEventListener('click', event => navigate(event, homeId));
  papersLink.addEventListener('click', event => navigate(event, 'real-world-p-values'));
  document.querySelector('.brand').addEventListener('click', event => navigate(event, homeId));
  document.querySelector('.create-callout').addEventListener('click', event => navigate(event, guideId));

  function groupEntries(items) {
    const groups = new Map();
    for (const entry of items) {
      if (!groups.has(entry.category)) groups.set(entry.category, []);
      groups.get(entry.category).push(entry);
    }
    return groups;
  }

  function collectionLink(entry) {
    const link = element('a', 'collection-link');
    link.href = `#${entry.id}`;
    link.dataset.visualization = entry.id;
    link.append(element('span', 'entry-title', entry.title), element('span', 'entry-description', entry.description));
    if (entry.id === 'real-world-p-values') link.querySelectorAll('span').forEach(formatPValues);
    if (entry.id === activeId) link.setAttribute('aria-current', 'page');
    link.addEventListener('click', event => navigate(event, entry.id));
    return link;
  }

  function renderGroups(container, items, prefix) {
    container.replaceChildren();
    let index = 0;
    for (const [category, group] of groupEntries(items)) {
      const section = element('section', 'collection-group');
      const heading = element('h3', 'group-heading', category);
      heading.id = `${prefix}-group-${index++}`;
      section.setAttribute('aria-labelledby', heading.id);
      const list = element('ul', 'collection-list');
      for (const entry of group) {
        const item = element('li');
        item.append(collectionLink(entry));
        list.append(item);
      }
      section.append(heading, list);
      container.append(section);
    }
  }

  function filterCollection() {
    const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const matches = entries.filter(entry => {
      const text = `${entry.title} ${entry.category} ${entry.description}`.toLocaleLowerCase();
      return terms.every(term => text.includes(term));
    });
    renderGroups(results, matches, 'browse');
    clearSearch.hidden = !search.value;
    document.querySelector('#search-status').textContent = terms.length
      ? `${matches.length} of ${entries.length} items`
      : `${visualizations.length} visualizations · ${guides.length} guide${guides.length === 1 ? '' : 's'}`;
    if (!matches.length) results.append(element('p', 'empty-state', entries.length
      ? 'No matches. Try another name or topic, or clear the search.'
      : 'No visualizations have been added yet.'));
  }

  function openBrowser(query = '') {
    search.value = query;
    filterCollection();
    dialog.showModal();
    browseButton.setAttribute('aria-expanded', 'true');
    document.body.classList.add('browse-open');
    syncVisibility();
    search.focus();
  }
  browseButton.addEventListener('click', () => openBrowser());
  document.querySelector('#browse-more').addEventListener('click', () => openBrowser());
  document.querySelector('#browse-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => {
    browseButton.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('browse-open');
    syncVisibility();
  });
  dialog.addEventListener('click', event => {
    const bounds = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < bounds.left || event.clientX > bounds.right
        || event.clientY < bounds.top || event.clientY > bounds.bottom)) dialog.close();
  });
  search.addEventListener('input', filterCollection);
  clearSearch.addEventListener('click', () => {
    search.value = '';
    filterCollection();
    search.focus();
  });

  for (const entry of entries) {
    const panel = element('section', `visualization-panel${entry.id === homeId ? ' home-feature' : ''}`);
    panel.id = `panel-${entry.id}`;
    panel.setAttribute('aria-label', entry.title);
    panel.tabIndex = -1;
    panel.hidden = true;
    panels.append(panel);
  }
  const visualizations = entries.filter(entry => entry.kind === 'visualization');
  const guides = entries.filter(entry => entry.kind === 'guide');
  document.querySelector('#browse-count').textContent = visualizations.length;
  document.querySelector('#collection-count').textContent = `${visualizations.length} visualizations, ready to explore and download.`;
  for (const [category, group] of groupEntries(visualizations)) {
    const button = element('button', 'topic-link', category);
    button.type = 'button';
    button.setAttribute('aria-haspopup', 'dialog');
    button.setAttribute('aria-controls', 'browse-dialog');
    button.append(element('span', '', `${group.length} visualization${group.length === 1 ? '' : 's'} →`));
    button.addEventListener('click', () => openBrowser(category));
    document.querySelector('#topic-links').append(button);
  }

  function notifyVisibility(frame, visible) {
    frame.contentWindow?.postMessage({type: 'stat250:visibility', visible}, window.location.origin);
  }

  function syncVisibility() {
    for (const {panel, frame} of mounted.values()) notifyVisibility(frame, !panel.hidden && !dialog.open);
  }

  function mount(entry) {
    const panel = document.querySelector(`#panel-${entry.id}`);
    const frame = element('iframe', 'visualization-frame');
    frame.title = entry.title;
    frame.src = entry.file;
    frame.addEventListener('load', () => {
      notifyVisibility(frame, !panel.hidden && !dialog.open);
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
    panel.append(frame, element('p', 'download-note', 'Download the HTML file to use or edit it offline.'));
    mounted.set(entry.id, {panel, frame});
    return panel;
  }

  function route() {
    let id;
    try { id = decodeURIComponent(window.location.hash.slice(1)) || homeId; }
    catch { id = ''; }
    if (id === 'home') id = homeId;
    if (id === 'overview') id = guideId; // Preserve links to the former guidance page.
    const unknown = entries.length > 0 && !allIds.includes(id);
    if (unknown) id = homeId;
    const notice = document.querySelector('#route-message');
    notice.hidden = !unknown;
    notice.textContent = unknown ? 'That visualization is not in the collection. Use Browse visualizations to choose another.' : '';
    const entry = entries.find(item => item.id === id);
    if (entry && !mounted.has(id)) mount(entry);
    document.querySelector('#home-collection').hidden = id !== homeId;
    for (const [key, value] of mounted) {
      value.panel.hidden = key !== id;
      notifyVisibility(value.frame, key === id && !dialog.open);
      if (key === id && value.resize) requestAnimationFrame(value.resize);
    }
    activeId = id;
    if (id === homeId) homeLink.setAttribute('aria-current', 'page');
    else homeLink.removeAttribute('aria-current');
    if (id === guideId) guideLink.setAttribute('aria-current', 'page');
    else guideLink.removeAttribute('aria-current');
    if (id === 'real-world-p-values') papersLink.setAttribute('aria-current', 'page');
    else papersLink.removeAttribute('aria-current');
    document.querySelectorAll('[data-visualization]').forEach(link => {
      if (link.dataset.visualization === id) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    const actions = document.querySelector('#visualization-actions');
    actions.hidden = !entry;
    if (entry) {
      const open = document.querySelector('#open-visualization');
      const download = document.querySelector('#download-visualization');
      open.href = entry.file;
      open.setAttribute('aria-label', `Open ${entry.title} on its own in a new tab`);
      download.href = entry.file;
      download.download = `stat250-${entry.id}.html`;
      download.setAttribute('aria-label', `Download ${entry.title} as a standalone HTML file`);
    }
    if (focusOnRoute) {
      (document.querySelector(`#panel-${id}`) || document.querySelector('#main')).focus({preventScroll: true});
      document.querySelector('.site-header').scrollIntoView({block: 'start'});
      focusOnRoute = false;
    }
    document.title = entry && id !== homeId ? `${entry.title} · ${site.title}` : `${site.title} · ${site.subtitle}`;
  }
  window.addEventListener('hashchange', route);
  route();

})();

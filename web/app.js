(() => {
  'use strict';

  const STORAGE_KEY = 'context-rollover-checkpoints-v1';
  const THEME_KEY = 'context-rollover-theme';
  const exampleState = {
    token_count: 3650,
    error_count: 1,
    context_usage_percent: 72,
    turn_count: 14,
    workflow: { phase: 'analysis', pending_items: 3 },
    notes: ['baseline captured', 'awaiting next step']
  };

  const $ = (id) => document.getElementById(id);
  const stateInput = $('stateInput');
  const checkpointSelect = $('checkpointSelect');
  const diffList = $('diffList');

  function loadCheckpoints() {
    try {
      const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {};
    } catch {
      return {};
    }
  }

  function persistCheckpoints(checkpoints) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(checkpoints));
  }

  function parseState() {
    let parsed;
    try {
      parsed = JSON.parse(stateInput.value);
    } catch (error) {
      throw new Error(`Invalid JSON: ${error.message}`);
    }
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error('State must be a JSON object.');
    }
    return parsed;
  }

  function numericValue(id) {
    const value = Number($(id).value);
    if (!Number.isFinite(value) || value < 0) throw new Error('Thresholds must be non-negative numbers.');
    return value;
  }

  function analyze() {
    const result = $('analysisResult');
    try {
      const state = parseState();
      const checks = [
        ['token_count', Number(state.token_count || 0), numericValue('tokenThreshold')],
        ['error_count', Number(state.error_count || 0), numericValue('errorThreshold')],
        ['context_usage_percent', Number(state.context_usage_percent || 0), numericValue('contextThreshold')],
        ['turn_count', Number(state.turn_count || 0), numericValue('turnThreshold')]
      ];
      const fired = checks.filter(([, value, threshold]) => value >= threshold).map(([name]) => name);
      result.classList.remove('is-triggered', 'is-clear');
      if (fired.length) {
        result.classList.add('is-triggered');
        result.textContent = `Rollover indicated by: ${fired.join(', ')}.`;
      } else {
        result.classList.add('is-clear');
        result.textContent = 'No configured rollover trigger fired.';
      }
    } catch (error) {
      result.classList.remove('is-clear');
      result.classList.add('is-triggered');
      result.textContent = error.message;
    }
  }

  function safeCheckpointId(raw) {
    const value = raw.trim();
    if (!value) throw new Error('Checkpoint ID is required.');
    if (!/^[A-Za-z0-9._-]{1,64}$/.test(value)) {
      throw new Error('Use only letters, numbers, dot, underscore, or hyphen in the checkpoint ID.');
    }
    return value;
  }

  function saveCheckpoint() {
    try {
      const id = safeCheckpointId($('checkpointId').value);
      const checkpoints = loadCheckpoints();
      checkpoints[id] = { state: parseState(), created_at: new Date().toISOString() };
      persistCheckpoints(checkpoints);
      refreshCheckpointList(id);
      $('checkpointMeta').textContent = `Saved ${id} at ${new Date(checkpoints[id].created_at).toLocaleString()}.`;
      activatePanel('checkpoint');
    } catch (error) {
      $('checkpointMeta').textContent = error.message;
    }
  }

  function refreshCheckpointList(preferredId) {
    const checkpoints = loadCheckpoints();
    const ids = Object.keys(checkpoints).sort((a, b) => checkpoints[b].created_at.localeCompare(checkpoints[a].created_at));
    checkpointSelect.replaceChildren();
    if (!ids.length) {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'No saved checkpoints';
      checkpointSelect.append(option);
    } else {
      ids.forEach((id) => {
        const option = document.createElement('option');
        option.value = id;
        option.textContent = id;
        checkpointSelect.append(option);
      });
      checkpointSelect.value = preferredId && checkpoints[preferredId] ? preferredId : ids[0];
    }
    $('checkpointCount').textContent = `${ids.length} saved`;
    renderCheckpointMeta();
  }

  function renderCheckpointMeta() {
    const id = checkpointSelect.value;
    const checkpoint = loadCheckpoints()[id];
    $('checkpointMeta').textContent = checkpoint
      ? `${id} - ${new Date(checkpoint.created_at).toLocaleString()}`
      : 'No checkpoint selected.';
  }

  function deleteCheckpoint() {
    const id = checkpointSelect.value;
    if (!id) return;
    const checkpoints = loadCheckpoints();
    delete checkpoints[id];
    persistCheckpoints(checkpoints);
    refreshCheckpointList();
  }

  function downloadCheckpoint() {
    const id = checkpointSelect.value;
    const checkpoint = loadCheckpoints()[id];
    if (!checkpoint) return;
    const blob = new Blob([JSON.stringify(checkpoint.state, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${id}.json`;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function compareValues(current, checkpoint, path = '') {
    const changes = [];
    const currentIsObject = current && typeof current === 'object';
    const checkpointIsObject = checkpoint && typeof checkpoint === 'object';

    if (Array.isArray(current) && Array.isArray(checkpoint)) {
      const length = Math.max(current.length, checkpoint.length);
      for (let index = 0; index < length; index += 1) {
        const nextPath = `${path}[${index}]`;
        if (index >= current.length) changes.push({ path: nextPath, type: 'added', current: undefined, checkpoint: checkpoint[index] });
        else if (index >= checkpoint.length) changes.push({ path: nextPath, type: 'removed', current: current[index], checkpoint: undefined });
        else changes.push(...compareValues(current[index], checkpoint[index], nextPath));
      }
      return changes;
    }

    if (currentIsObject && checkpointIsObject && !Array.isArray(current) && !Array.isArray(checkpoint)) {
      const keys = [...new Set([...Object.keys(current), ...Object.keys(checkpoint)])].sort();
      for (const key of keys) {
        const nextPath = path ? `${path}.${key}` : key;
        if (!(key in current)) changes.push({ path: nextPath, type: 'added', current: undefined, checkpoint: checkpoint[key] });
        else if (!(key in checkpoint)) changes.push({ path: nextPath, type: 'removed', current: current[key], checkpoint: undefined });
        else changes.push(...compareValues(current[key], checkpoint[key], nextPath));
      }
      return changes;
    }

    if (JSON.stringify(current) !== JSON.stringify(checkpoint)) {
      changes.push({ path: path || '(root)', type: 'modified', current, checkpoint });
    }
    return changes;
  }

  function compareCheckpoint() {
    try {
      const id = checkpointSelect.value;
      const checkpoint = loadCheckpoints()[id];
      if (!checkpoint) throw new Error('Select or save a checkpoint first.');
      const changes = compareValues(parseState(), checkpoint.state);
      const counts = changes.reduce((acc, item) => {
        acc[item.type] += 1;
        return acc;
      }, { added: 0, removed: 0, modified: 0 });
      $('addedCount').textContent = counts.added;
      $('removedCount').textContent = counts.removed;
      $('modifiedCount').textContent = counts.modified;
      diffList.replaceChildren();
      if (!changes.length) {
        const empty = document.createElement('div');
        empty.className = 'empty-state';
        empty.textContent = 'Current state matches the selected checkpoint.';
        diffList.append(empty);
      } else {
        changes.forEach((change) => {
          const row = document.createElement('div');
          row.className = 'diff-row';
          const kind = document.createElement('span');
          kind.className = `diff-kind ${change.type}`;
          kind.textContent = change.type;
          const path = document.createElement('code');
          path.textContent = change.path;
          const value = document.createElement('code');
          value.textContent = `current=${JSON.stringify(change.current)} -> checkpoint=${JSON.stringify(change.checkpoint)}`;
          row.append(kind, path, value);
          diffList.append(row);
        });
      }
      activatePanel('diff');
    } catch (error) {
      diffList.replaceChildren();
      const empty = document.createElement('div');
      empty.className = 'empty-state';
      empty.textContent = error.message;
      diffList.append(empty);
      activatePanel('diff');
    }
  }

  function activatePanel(name) {
    document.querySelectorAll('[data-panel]').forEach((panel) => panel.classList.toggle('is-active', panel.dataset.panel === name));
    document.querySelectorAll('[data-panel-target]').forEach((button) => button.classList.toggle('is-active', button.dataset.panelTarget === name));
  }

  function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(THEME_KEY, theme);
    $('themeToggle').textContent = theme === 'dark' ? 'Light' : 'Dark';
  }

  stateInput.value = JSON.stringify(exampleState, null, 2);
  const storedTheme = localStorage.getItem(THEME_KEY);
  setTheme(storedTheme === 'dark' || storedTheme === 'light'
    ? storedTheme
    : (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  refreshCheckpointList();

  $('analyzeButton').addEventListener('click', analyze);
  $('saveCheckpoint').addEventListener('click', saveCheckpoint);
  $('deleteCheckpoint').addEventListener('click', deleteCheckpoint);
  $('downloadCheckpoint').addEventListener('click', downloadCheckpoint);
  $('compareButton').addEventListener('click', compareCheckpoint);
  checkpointSelect.addEventListener('change', renderCheckpointMeta);
  $('loadExample').addEventListener('click', () => { stateInput.value = JSON.stringify(exampleState, null, 2); analyze(); });
  $('themeToggle').addEventListener('click', () => setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));
  document.querySelectorAll('[data-panel-target]').forEach((button) => button.addEventListener('click', () => activatePanel(button.dataset.panelTarget)));
})();

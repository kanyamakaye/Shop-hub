// Cascading Province -> District -> Sector -> Cell -> Village selects,
// populated from static/data/rwanda_locations.json.
// Exposed as window.initLocationCascade() so it can be re-run after a
// form is injected into a modal (no DOMContentLoaded event fires then).
window.initLocationCascade = function initLocationCascade(root) {
    root = root || document;
    const LEVELS = ['province', 'district', 'sector', 'cell', 'village'];
    const selects = {};
    LEVELS.forEach((level) => {
        selects[level] = root.querySelector(`[data-level="${level}"]`);
    });
    if (!selects.province || selects.province.dataset.cascadeBound) return;
    selects.province.dataset.cascadeBound = 'true';

    const dataUrl = selects.province.dataset.source || '/static/data/rwanda_locations.json';

    function fillSelect(select, options, placeholder) {
        select.innerHTML = '';
        const empty = document.createElement('option');
        empty.value = '';
        empty.textContent = placeholder;
        select.appendChild(empty);
        options.forEach((name) => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            select.appendChild(option);
        });
    }

    fetch(dataUrl)
        .then((response) => response.json())
        .then((locations) => {
            const initial = {};
            LEVELS.forEach((level) => { initial[level] = selects[level].dataset.initial || ''; });

            fillSelect(selects.province, Object.keys(locations), 'Select province...');

            function cascadeFrom(level) {
                const index = LEVELS.indexOf(level);
                for (let i = index + 1; i < LEVELS.length; i += 1) {
                    fillSelect(selects[LEVELS[i]], [], `Select ${LEVELS[i]}...`);
                }
                const node = getNode(locations, index);
                if (!node) return;
                const nextLevel = LEVELS[index + 1];
                if (nextLevel) {
                    const options = Array.isArray(node) ? [] : Object.keys(node);
                    fillSelect(selects[nextLevel], options, `Select ${nextLevel}...`);
                }
            }

            function getNode(locations, upToIndex) {
                let node = locations;
                for (let i = 0; i <= upToIndex; i += 1) {
                    const value = selects[LEVELS[i]].value;
                    if (!value || !node) return null;
                    node = node[value];
                }
                return node;
            }

            LEVELS.forEach((level) => {
                selects[level].addEventListener('change', () => cascadeFrom(level));
            });

            // Pre-fill for edit forms: walk the saved values level by level.
            if (initial.province && locations[initial.province]) {
                selects.province.value = initial.province;
                cascadeFrom('province');
                if (initial.district) {
                    selects.district.value = initial.district;
                    cascadeFrom('district');
                    if (initial.sector) {
                        selects.sector.value = initial.sector;
                        cascadeFrom('sector');
                        if (initial.cell) {
                            selects.cell.value = initial.cell;
                            cascadeFrom('cell');
                            if (initial.village) selects.village.value = initial.village;
                        }
                    }
                }
            }
        });
};

document.addEventListener('DOMContentLoaded', () => window.initLocationCascade());

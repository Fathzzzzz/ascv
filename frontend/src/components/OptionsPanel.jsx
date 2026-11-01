import { CHARSETS, MODES } from "../constants.js";

function currentMode(mode) {
  return MODES.find((item) => item.value === mode) ?? MODES[0];
}

export { currentMode };

export default function OptionsPanel({ options, onChange, disabled }) {
  const mode = currentMode(options.mode);

  function changeMode(nextMode) {
    const next = currentMode(nextMode);
    onChange({
      ...options,
      mode: next.value,
      width: next.defaultWidth,
      charset: CHARSETS[next.value][0].value,
    });
  }

  return (
    <section className="panel" aria-labelledby="options-title">
      <h2 id="options-title" className="panel__title">
        Opsi
      </h2>

      <div className="field">
        <span className="field__label">Mode</span>
        <div className="segmented" role="radiogroup" aria-label="Mode keluaran">
          {MODES.map((item) => (
            <button
              key={item.value}
              type="button"
              role="radio"
              aria-checked={options.mode === item.value}
              className={`segmented__item${options.mode === item.value ? " segmented__item--active" : ""}`}
              onClick={() => changeMode(item.value)}
              disabled={disabled}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <label className="field__label" htmlFor="width">
          Lebar ({mode.minWidth}–{mode.maxWidth} kolom)
        </label>
        <input
          id="width"
          className="field__input"
          type="number"
          inputMode="numeric"
          min={mode.minWidth}
          max={mode.maxWidth}
          step={1}
          value={options.width}
          disabled={disabled}
          onChange={(event) => {
            const parsed = Number.parseInt(event.target.value, 10);
            onChange({ ...options, width: Number.isNaN(parsed) ? "" : parsed });
          }}
        />
      </div>

      <div className="field">
        <label className="field__label" htmlFor="charset">
          Charset
        </label>
        <select
          id="charset"
          className="field__input"
          value={options.charset}
          disabled={disabled}
          onChange={(event) => onChange({ ...options, charset: event.target.value })}
        >
          {CHARSETS[options.mode].map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </div>

      <label className="checkbox">
        <input
          type="checkbox"
          checked={options.invert}
          disabled={disabled}
          onChange={(event) => onChange({ ...options, invert: event.target.checked })}
        />
        <span>Invert (balik gelap dan terang)</span>
      </label>

      <label className="checkbox">
        <input
          type="checkbox"
          checked={options.removeBg}
          disabled={disabled}
          onChange={(event) => onChange({ ...options, removeBg: event.target.checked })}
        />
        <span>Hapus latar belakang</span>
      </label>
    </section>
  );
}

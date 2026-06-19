/**
 * FilterBar — day phase, UTC day, and visibility filters.
 */
function FilterBar({ filters, onChange, onApply, disabled }) {
  function handleChange(field, value) {
    onChange({ ...filters, [field]: value });
  }

  return (
    <fieldset className="filter-bar" disabled={disabled}>
      <legend>Filter Images</legend>

      <div className="filter-controls">
        <div className="filter-field">
          <label htmlFor="filter-day-phase">Day Phase</label>
          <select
            id="filter-day-phase"
            value={filters.day_phase}
            onChange={(e) => handleChange('day_phase', e.target.value)}
          >
            <option value="">All</option>
            <option value="night">Night</option>
            <option value="dawn">Dawn</option>
            <option value="day">Day</option>
            <option value="dusk">Dusk</option>
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="filter-utc-day">UTC Day</label>
          <input
            id="filter-utc-day"
            type="text"
            value={filters.utc_day}
            onChange={(e) => handleChange('utc_day', e.target.value)}
            placeholder="e.g. 2026.170"
            pattern="[0-9]{4}\.[0-9]{3}"
          />
        </div>

        <div className="filter-field">
          <label htmlFor="filter-visibility">Visibility</label>
          <select
            id="filter-visibility"
            value={filters.visibility}
            onChange={(e) => handleChange('visibility', e.target.value)}
          >
            <option value="">All</option>
            <option value="daylight">Daylight</option>
            <option value="low_light">Low light</option>
            <option value="night">Night</option>
          </select>
        </div>

        <div className="filter-field">
          <button type="button" onClick={onApply}>
            Apply Filters
          </button>
        </div>
      </div>
    </fieldset>
  );
}

export default FilterBar;

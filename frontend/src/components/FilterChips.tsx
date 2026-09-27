type FilterChipsProps<T extends string> = {
  label: string;
  options: { value: T; label: string; count?: number }[];
  value: T;
  onChange: (value: T) => void;
};

export function FilterChips<T extends string>({
  label,
  options,
  value,
  onChange,
}: FilterChipsProps<T>) {
  return (
    <div className="chips" role="group" aria-label={label}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          className="chip"
          aria-pressed={option.value === value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
          {option.count !== undefined && <span className="chip__count">{option.count}</span>}
        </button>
      ))}
    </div>
  );
}

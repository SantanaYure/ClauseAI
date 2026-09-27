import { Icon } from './Icon';

type SearchFieldProps = {
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
};

export function SearchField({ label, placeholder, value, onChange }: SearchFieldProps) {
  return (
    <label className="search-field">
      <span className="visually-hidden">{label}</span>
      <Icon name="search" size={20} />
      <input
        type="search"
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

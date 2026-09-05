import { forwardRef } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
}

export const SearchBar = forwardRef<HTMLInputElement, Props>(function SearchBar(
  { value, onChange },
  ref
) {
  return (
    <div className="ec-searchwrap">
      <div className="ec-searchbox">
        <span className="ec-searchbox__icon">🔍</span>
        <input
          ref={ref}
          className="ec-searchbox__input"
          type="text"
          value={value}
          placeholder="名前・IP・メモ・タグで検索"
          onChange={(e) => onChange(e.target.value)}
        />
        <span className="ec-searchbox__hint">Ctrl K</span>
      </div>
    </div>
  );
});

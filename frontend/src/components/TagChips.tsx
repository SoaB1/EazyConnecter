interface TagCount {
  tag: string;
  count: number;
}

interface Props {
  tags: TagCount[];
  activeTag: string;
  onToggle: (tag: string) => void;
}

export function TagChips({ tags, activeTag, onToggle }: Props) {
  if (tags.length === 0) return null;
  return (
    <div className="ec-tagchips">
      {tags.map(({ tag, count }) => {
        const active = tag === activeTag;
        return (
          <button
            key={tag}
            className={`ec-tagchip${active ? " ec-tagchip--active" : ""}`}
            onClick={() => onToggle(tag)}
          >
            {tag}
            <span className="ec-tagchip__count">{count}</span>
          </button>
        );
      })}
    </div>
  );
}

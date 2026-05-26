interface BottomNavProps {
  activeSection: string;
  onNavigate: (section: string) => void;
}

const NAV_ITEMS = [
  {
    key: 'overview',
    label: 'Overview',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="2" width="7" height="7" rx="1.5" />
        <rect x="11" y="2" width="7" height="7" rx="1.5" />
        <rect x="2" y="11" width="7" height="7" rx="1.5" />
        <rect x="11" y="11" width="7" height="7" rx="1.5" />
      </svg>
    ),
  },
  {
    key: 'applications',
    label: 'Pipeline',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <line x1="3" y1="5" x2="17" y2="5" />
        <line x1="3" y1="10" x2="17" y2="10" />
        <line x1="3" y1="15" x2="13" y2="15" />
      </svg>
    ),
  },
  {
    key: 'suggested',
    label: 'Jobs',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="6" width="14" height="11" rx="2" />
        <path d="M7 6V4a3 3 0 0 1 6 0v2" />
      </svg>
    ),
  },
  {
    key: 'insights',
    label: 'Insights',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="3,15 7,9 11,12 17,5" />
        <polyline points="13,5 17,5 17,9" />
      </svg>
    ),
  },
];

export function BottomNav({ activeSection, onNavigate }: BottomNavProps) {
  return (
    <nav className="bottom-nav" aria-label="Section navigation">
      {NAV_ITEMS.map((item) => (
        <button
          key={item.key}
          type="button"
          className={`bottom-nav__item${activeSection === item.key ? ' is-active' : ''}`}
          onClick={() => onNavigate(item.key)}
          aria-label={item.label}
        >
          {item.icon}
          <span className="bottom-nav__label">{item.label}</span>
        </button>
      ))}
    </nav>
  );
}

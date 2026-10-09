const icons = [
  <path key="bolt" d="m16 3-8 10h6l-2 8 8-11h-6l2-7Z" />,
  <path key="spark" d="m12 3 1.7 6.3L20 11l-6.3 1.7L12 19l-1.7-6.3L4 11l6.3-1.7L12 3Z" />,
  <><path key="slab" d="M7 5h10l3 3v8l-3 3H7l-3-3V8l3-3Z" /><path key="slab-line" d="M8 12h8" /></>,
  <path key="interlock" d="M10 8.5 8.2 6.7a3 3 0 0 0-4.2 4.2l3 3a3 3 0 0 0 4.2 0l1.3-1.3M14 15.5l1.8 1.8a3 3 0 0 0 4.2-4.2l-3-3a3 3 0 0 0-4.2 0l-1.3 1.3" />,
  <><circle key="dot-1" cx="7" cy="8" r="1.5" /><circle key="dot-2" cx="12" cy="5" r="1.5" /><circle key="dot-3" cx="17" cy="8" r="1.5" /><circle key="dot-4" cx="9" cy="14" r="1.5" /><circle key="dot-5" cx="15" cy="15" r="1.5" /></>,
  <path key="spiral" d="M18.5 9.2c0-3.3-3-5.7-6.5-5.1-4.7.8-6.9 6-4.1 9.6 2.8 3.5 8.8 2.8 10.2-1.5 1.2-3.5-2.2-6.8-5.5-5.4-2.5 1-2.5 4.7.1 5.2 1.8.3 2.9-1.6 1.8-2.6" />,
];

export default function ToolIcons() {
  return (
    <div className="tool-icons" aria-hidden="true">
      {icons.map((icon, index) => (
        <span className="tool-icon" key={index} aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
            {icon}
          </svg>
        </span>
      ))}
    </div>
  );
}

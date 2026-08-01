// Hard link components for TheMoneytizer compatibility
// These force full page reloads to ensure ads load correctly

export function ArticleLink({ to, children, className, ...props }) {
  return (
    <a href={to} className={className} {...props}>
      {children}
    </a>
  );
}

export function PlayerLink({ slug, children, className, ...props }) {
  return (
    <a href={`/spieler/${slug}`} className={className} {...props}>
      {children}
    </a>
  );
}

export function ClubLink({ slug, children, className, ...props }) {
  return (
    <a href={`/verein/${slug}`} className={className} {...props}>
      {children}
    </a>
  );
}

export function NavLink({ to, children, className, onClick, ...props }) {
  return (
    <a href={to} className={className} onClick={onClick} {...props}>
      {children}
    </a>
  );
}

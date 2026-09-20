import { Link } from "react-router-dom";
import { User, Buildings, ArrowRight } from "@phosphor-icons/react";
import { safeRelatedLink } from '@/lib/relatedLink';

export function RelatedLinks({ links = [], className = "" }) {
  if (!links || links.length === 0) return null;

  const validLinks = links.map(link => ({ ...link, url: safeRelatedLink(link) })).filter(link => link.url);
  if (!validLinks.length) return null;
  const playerLinks = validLinks.filter(l => l.type === 'player');
  const clubLinks = validLinks.filter(l => l.type === 'club');

  return (
    <div className={`bg-gray-50 border border-gray-200 p-4 ${className}`} data-testid="related-links">
      <h3 className="text-sm font-bold uppercase text-gray-700 mb-3 flex items-center gap-2">
        <ArrowRight size={14} weight="bold" className="text-[#79B92A]" />
        Mehr zu diesem Thema
      </h3>

      <div className="flex flex-wrap gap-2">
        {playerLinks.map((link) => (
          <Link
            key={link.url}
            to={link.url}
            className="inline-flex items-center gap-1.5 bg-white border border-gray-200 px-3 py-1.5 text-sm hover:border-[#79B92A] hover:text-[#79B92A] transition-colors"
            data-testid={`related-player-${link.name}`}
          >
            <User size={14} weight="bold" />
            <span>{link.name}</span>
          </Link>
        ))}

        {clubLinks.map((link) => (
          <Link
            key={link.url}
            to={link.url}
            className="inline-flex items-center gap-1.5 bg-white border border-gray-200 px-3 py-1.5 text-sm hover:border-[#79B92A] hover:text-[#79B92A] transition-colors"
            data-testid={`related-club-${link.name}`}
          >
            <Buildings size={14} weight="bold" />
            <span>{link.name}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default RelatedLinks;

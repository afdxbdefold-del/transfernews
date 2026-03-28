/**
 * Schema.org JSON-LD Components for SEO
 * Uses React's dangerouslySetInnerHTML which properly renders in SSR and CSR
 */

export function PersonSchema({ person }) {
  if (!person) return null;
  
  const schema = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": person.name,
    "url": person.url,
    ...(person.nationality && { "nationality": person.nationality }),
    ...(person.birthDate && { "birthDate": person.birthDate }),
    ...(person.image && { "image": person.image }),
    ...(person.jobTitle && { "jobTitle": person.jobTitle })
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

export function SportsTeamSchema({ team }) {
  if (!team) return null;
  
  const schema = {
    "@context": "https://schema.org",
    "@type": "SportsTeam",
    "name": team.name,
    "url": team.url,
    "sport": "Fußball",
    ...(team.location && { "location": { "@type": "Place", "name": team.location } }),
    ...(team.logo && { "logo": team.logo })
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

export function WebsiteSchema() {
  const schema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "TransferNews.de",
    "url": "https://transfernews.de",
    "description": "Die neuesten Fußball-Transfer-News, Gerüchte und offizielle Wechsel",
    "potentialAction": {
      "@type": "SearchAction",
      "target": "https://transfernews.de/suche?q={search_term_string}",
      "query-input": "required name=search_term_string"
    }
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

export default { PersonSchema, SportsTeamSchema, WebsiteSchema };

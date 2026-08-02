interface Props {
  language: string;
  onChange: (lang: string) => void;
}

const LANGUAGES: Record<string, string> = {
  Español: "es",
  English: "en",
  Français: "fr",
  Deutsch: "de",
  Português: "pt",
  Italiano: "it",
};

export default function LanguageSelector({ language, onChange }: Props) {
  return (
    <select
      value={language}
      onChange={(e) => onChange(e.target.value)}
      className="lang-select"
    >
      {Object.entries(LANGUAGES).map(([name, code]) => (
        <option key={code} value={code}>
          {name}
        </option>
      ))}
    </select>
  );
}

/** エラー文の表示。message が空なら何も表示しない。 */
export function ErrorMessage({
  message,
  className = "text-sm",
}: {
  message: string | null | undefined;
  className?: string;
}) {
  if (!message) return null;
  return (
    <p role="alert" className={`text-red-600 ${className}`}>
      {message}
    </p>
  );
}

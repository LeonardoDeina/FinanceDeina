export function Loading() {
  return <div className="feedback">Carregando...</div>
}

export function ErrorMessage({ message }: { message: string }) {
  return <div className="feedback feedback-error">{message}</div>
}

export function EmptyState({ message }: { message: string }) {
  return <div className="feedback muted">{message}</div>
}

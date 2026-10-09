export function Card({ className = '', children }) {
  return <div className={`card ${className}`.trim()}>{children}</div>
}

export function CardHeader({ children }) {
  return <div className="card-header">{children}</div>
}

export function CardBody({ className = '', children }) {
  return <div className={`card-body ${className}`.trim()}>{children}</div>
}

export function CardFooter({ children }) {
  return <div className="card-footer">{children}</div>
}

export default Card
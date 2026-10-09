export default function Button({
  as: Tag = 'button',
  variant = 'default',
  size,
  block = false,
  loading = false,
  className = '',
  children,
  disabled,
  ...props
}) {
  const classes = [
    'btn',
    variant !== 'default' && `btn--${variant}`,
    size && `btn--${size}`,
    block && 'btn--block',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  const isButton = Tag === 'button'
  return (
    <Tag className={classes} disabled={isButton ? disabled || loading : undefined} {...props}>
      {loading ? <span className="spinner" aria-hidden="true" /> : children}
    </Tag>
  )
}
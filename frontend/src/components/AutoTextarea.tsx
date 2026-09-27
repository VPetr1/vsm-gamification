import { useLayoutEffect, useRef, type TextareaHTMLAttributes } from "react";

/** A textarea that grows and shrinks with its content, so long texts need no inner scrolling. */
export function AutoTextarea({ minRows = 2, style, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement> & { minRows?: number }) {
  const ref = useRef<HTMLTextAreaElement>(null);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight + (el.offsetHeight - el.clientHeight)}px`;
  }, [props.value]);
  return <textarea ref={ref} rows={minRows} style={{ resize: "vertical", overflow: "hidden", ...style }} {...props} />;
}

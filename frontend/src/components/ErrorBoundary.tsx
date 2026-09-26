import { Component, type ReactNode } from "react";

type State = { failed: boolean };

/** Keeps one broken page from blanking the whole app; resets when the route changes (via key). */
export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch(error: unknown) {
    console.error("Ошибка интерфейса", error);
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="state state-error" role="alert">
          <p>На странице произошла ошибка. Данные на сервере не изменены.</p>
          <button type="button" className="btn btn-secondary" onClick={() => window.location.reload()}>
            Перезагрузить страницу
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

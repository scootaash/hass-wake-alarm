import { css } from "lit";

/** CSS shared between the main and settings views. */
export const sharedStyles = css`
  :host {
    --wa-gap: 16px;
    --wa-radius: 12px;
    --wa-chip-size: 44px;
    --wa-section-gap: 20px;
  }

  ha-card {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: var(--wa-section-gap);
  }

  .header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .header .title {
    flex: 1;
    font-size: 1.1rem;
    font-weight: 500;
  }

  .header ha-icon-button {
    --mdc-icon-button-size: 36px;
    color: var(--secondary-text-color);
  }

  .row {
    display: flex;
    align-items: center;
    gap: var(--wa-gap);
  }

  .label {
    flex: 1;
    color: var(--primary-text-color);
    font-size: 0.95rem;
  }

  .value {
    font-variant-numeric: tabular-nums;
    color: var(--secondary-text-color);
  }

  button.btn,
  .btn {
    background: var(--ha-card-background, var(--card-background-color));
    border: 1px solid var(--divider-color);
    color: var(--primary-text-color);
    border-radius: var(--wa-radius);
    padding: 8px 16px;
    font-size: 0.95rem;
    cursor: pointer;
    font-family: inherit;
  }
  button.btn:hover {
    background: var(--secondary-background-color);
  }
  button.btn[disabled] {
    opacity: 0.5;
    cursor: not-allowed;
  }
  button.btn.primary {
    background: var(--primary-color);
    color: var(--text-primary-color);
    border-color: var(--primary-color);
  }
  button.btn.danger {
    background: rgb(255, 82, 82);
    color: white;
    border-color: rgb(255, 82, 82);
  }

  .error {
    color: var(--error-color, rgb(255, 82, 82));
    padding: 16px;
    font-size: 0.95rem;
  }
  .loading {
    padding: 16px;
    color: var(--secondary-text-color);
  }
`;

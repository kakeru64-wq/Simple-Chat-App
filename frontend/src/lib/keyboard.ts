import type { KeyboardEvent } from "react";

/**
 * 日本語入力（IME）の変換中か。変換確定の Enter で送信・保存してしまわないために使う。
 * keyCode 229 は isComposing を正しく返さない一部ブラウザ向けのフォールバック。
 */
export function isImeComposing(e: KeyboardEvent): boolean {
  return e.nativeEvent.isComposing || e.keyCode === 229;
}

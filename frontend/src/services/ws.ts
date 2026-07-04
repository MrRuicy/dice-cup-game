// WebSocket 封装：单例连接、自动重连（指数退避）、消息分发
import type { ClientMessage, ServerMessage } from '../types';

type MessageHandler = (msg: ServerMessage) => void;

class WsClient {
  private ws: WebSocket | null = null;
  private handler: MessageHandler | null = null;
  private reconnectDelay = 1000;
  private readonly maxDelay = 8000;
  private shouldReconnect = true;
  private onReconnect: (() => void) | null = null;
  private messageQueue: ClientMessage[] = []; // 等待发送的消息队列

  /** 建立连接。onMessage 分发所有服务端消息；onReconnect 在重连成功后触发（用于补发 reconnect 指令）。 */
  connect(onMessage: MessageHandler, onReconnect?: () => void): void {
    this.handler = onMessage;
    this.onReconnect = onReconnect ?? null;
    this.shouldReconnect = true;
    this.open();
  }

  private open(): void {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${proto}://${location.host}/ws`;
    const ws = new WebSocket(url);
    this.ws = ws;

    ws.onopen = () => {
      this.reconnectDelay = 1000;
      // 连接成功后触发回调（首次和重连都触发，让上层决定是否发送 reconnect 消息）
      if (this.onReconnect) this.onReconnect();
      // 发送队列中的消息
      this.flushQueue();
    };

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data) as ServerMessage;
        this.handler?.(msg);
      } catch {
        // 忽略非法消息
      }
    };

    ws.onclose = () => {
      this.ws = null;
      if (this.shouldReconnect) this.scheduleReconnect();
    };

    ws.onerror = () => {
      ws.close();
    };
  }

  private scheduleReconnect(): void {
    // 标记为非首次，open 里据此触发 onReconnect
    this.reconnectDelay = Math.min(this.reconnectDelay * 1.6, this.maxDelay);
    setTimeout(() => {
      if (this.shouldReconnect) this.open();
    }, this.reconnectDelay);
  }

  send(msg: ClientMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    } else {
      this.messageQueue.push(msg);
    }
  }

  private flushQueue(): void {
    if (this.messageQueue.length === 0) return;
    while (this.messageQueue.length > 0) {
      const msg = this.messageQueue.shift()!;
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(msg));
      }
    }
  }

  close(): void {
    this.shouldReconnect = false;
    this.ws?.close();
    this.ws = null;
  }
}

export const wsClient = new WsClient();

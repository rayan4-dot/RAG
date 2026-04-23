import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './ChatInterface.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  metrics?: {
    retrieval_latency?: number;
    total_latency?: number;
  };
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! Upload a document first, then ask me anything about it.',
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    
    const newUserMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
    };
    
    setMessages((prev) => [...prev, newUserMsg]);
    setIsLoading(true);

    // Initial bot message that we'll update as chunks arrive
    const botMsgId = (Date.now() + 1).toString();
    const initialBotMsg: Message = {
      id: botMsgId,
      role: 'assistant',
      content: '',
      sources: [],
    };
    
    setMessages((prev) => [...prev, initialBotMsg]);

    try {
      const response = await fetch('/api/stream-query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: userMessage }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get stream');
      }

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let finished = false;
      let accumulatedContent = '';

      while (!finished) {
        const { value, done } = await reader.read();
        if (done) {
          finished = true;
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            
            if (dataStr === '[DONE]') {
              finished = true;
              break;
            }

            try {
              const data = JSON.parse(dataStr);
              
              if (data.type === 'content') {
                accumulatedContent += data.data;
                setMessages((prev) => 
                  prev.map((msg) => 
                    msg.id === botMsgId ? { ...msg, content: accumulatedContent } : msg
                  )
                );
              } else if (data.type === 'sources') {
                setMessages((prev) => 
                  prev.map((msg) => 
                    msg.id === botMsgId ? { ...msg, sources: data.data } : msg
                  )
                );
              } else if (data.type === 'metrics') {
                setMessages((prev) => 
                  prev.map((msg) => 
                    msg.id === botMsgId ? { ...msg, metrics: { ...msg.metrics, ...data.data } } : msg
                  )
                );
              }
            } catch (e) {
              // Ignore empty or malformed JSON chunks
            }
          }
        }
      }

    } catch (error: any) {
      setMessages((prev) => 
        prev.map((msg) => 
          msg.id === botMsgId 
            ? { ...msg, content: `**Error:** ${error.message}` } 
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container glass-panel animate-fade-in">
      <div className="messages-area">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-wrapper ${msg.role}`}>
            <div className="avatar">
              {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
            </div>
            <div className="message-content">
              <div className="markdown-body">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
              
              {msg.role === 'assistant' && msg.metrics && (
                <div className="message-metrics">
                  {msg.metrics.retrieval_latency && (
                    <span className="metric-tag">Retrieval: {msg.metrics.retrieval_latency}ms</span>
                  )}
                  {msg.metrics.total_latency && (
                    <span className="metric-tag">Total: {msg.metrics.total_latency}ms</span>
                  )}
                </div>
              )}

              {msg.sources && msg.sources.length > 0 && (
                <div className="sources-container">
                  <span className="sources-label">Sources:</span>
                  <ul className="sources-list">
                    {msg.sources.map((src, idx) => (
                      <li key={idx}>{src}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-wrapper assistant">
            <div className="avatar">
              <Bot size={20} />
            </div>
            <div className="message-content loading">
              <Loader2 className="animate-spin" size={20} />
              <span>Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form className="input-area" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your documents..."
          disabled={isLoading}
        />
        <button type="submit" className="btn-send" disabled={!input.trim() || isLoading}>
          <Send size={20} />
        </button>
      </form>
    </div>
  );
}

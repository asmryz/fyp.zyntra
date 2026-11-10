import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'
import { Alert } from './ui/Feedback'
import Icon from './ui/Icon'

/**
 * Chat panel for the AI admission assistant. The backend forwards questions
 * to the LangGraph/RAG service when AI_SERVICE_URL is configured; until then
 * the panel explains that the assistant is not connected.
 *
 * This panel used to sit on the student Admission Guidance page, which has
 * been removed. It is kept here, unused, so it can be placed on another
 * student page once the AI service is connected.
 */
export default function AssistantPanel() {
  const status = useApi('/api/student/assistant/status')
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState(null)
  const available = status.data?.available

  async function handleAsk(event) {
    event.preventDefault()
    const text = question.trim()
    if (text.length < 3) return
    setAsking(true)
    setError(null)
    setMessages((current) => [...current, { from: 'user', text }])
    setQuestion('')
    try {
      const answer = await api.post('/api/student/assistant/ask', { question: text })
      setMessages((current) => [...current, { from: 'assistant', text: answer.answer, sources: answer.sources }])
    } catch (err) {
      setError(err.message)
    } finally {
      setAsking(false)
    }
  }

  return (
    <section className="panel" aria-labelledby="assistant-title">
      <div className="panel-head">
        <h2 id="assistant-title" className="panel-title">
          Ask ZYNTRA
        </h2>
        {status.data && (
          <span className={`badge ${available ? 'badge-published' : 'badge-draft'}`}>
            {available ? 'Connected' : 'Not connected yet'}
          </span>
        )}
      </div>

      {status.data && !available && <Alert type="info">{status.data.message}</Alert>}

      {available && (
        <>
          <p className="field-hint" style={{ marginBottom: 12 }}>
            Answers come from approved admission sources and are guidance only.
          </p>
          {messages.length > 0 && (
            <div className="chat-log" aria-live="polite">
              {messages.map((message, index) => (
                <div key={index} className={`chat-message from-${message.from}`}>
                  {message.text}
                  {message.sources?.length > 0 && (
                    <span className="cell-secondary" style={{ marginTop: 8 }}>
                      Sources: {message.sources.join(', ')}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
          <Alert type="error">{error}</Alert>
          <form className="chat-form" onSubmit={handleAsk}>
            <label htmlFor="assistant-question" className="sr-only">
              Your admission question
            </label>
            <input
              id="assistant-question"
              className="input"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="e.g. What documents do I need for the BS Computer Science program?"
              maxLength={1000}
            />
            <button type="submit" className="btn btn-primary" disabled={asking || question.trim().length < 3}>
              {asking ? <span className="spinner" aria-hidden="true" /> : <Icon name="send" size={18} />}
              <span className="sr-only">Send question</span>
            </button>
          </form>
        </>
      )}
    </section>
  )
}

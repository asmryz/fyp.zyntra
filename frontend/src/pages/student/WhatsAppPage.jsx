import { PageHeader } from '../../components/layout/DashboardLayout'
import { Alert, PageLoader } from '../../components/ui/Feedback'
import Icon from '../../components/ui/Icon'
import { useApi } from '../../hooks/useApi'
import { usePageTitle } from '../../hooks/usePageTitle'

export default function WhatsAppPage() {
  usePageTitle('WhatsApp assistance')
  const { data, error, loading } = useApi('/api/student/whatsapp')

  return (
    <>
      <PageHeader
        title="Admission help on WhatsApp"
        description="Ask ZYNTRA admission questions from WhatsApp. Answers use the same approved sources as the website."
      />
      {loading && <PageLoader />}
      {error && <Alert type="error">{error.message}</Alert>}

      {data && (
        <div className="two-column two-column-wide">
          <section className="panel" aria-labelledby="whatsapp-status">
            <div className="panel-head">
              <h2 id="whatsapp-status" className="panel-title">
                ZYNTRA on WhatsApp
              </h2>
              <span className={`badge ${data.configured ? 'badge-published' : 'badge-draft'}`}>
                {data.configured ? 'Available' : 'Not connected yet'}
              </span>
            </div>
            {data.configured ? (
              <>
                <p>
                  Save <strong style={{ color: 'var(--text)' }}>{data.number}</strong> in your contacts or open the chat
                  directly.
                </p>
                <a
                  href={data.chat_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-primary"
                  style={{ marginTop: 16 }}
                >
                  <Icon name="chat" size={18} /> Open WhatsApp chat
                  <span className="sr-only"> (opens in a new tab)</span>
                </a>
              </>
            ) : (
              <Alert type="info">
                <p>
                  The WhatsApp assistant has not been connected yet. Once it is available, the number and a chat link
                  will appear here.
                </p>
              </Alert>
            )}
          </section>

          <section className="panel" aria-labelledby="whatsapp-how">
            <h2 id="whatsapp-how" className="panel-title">
              How it works
            </h2>
            <ol className="check-list" style={{ marginTop: 0 }}>
              <li>
                <span className="check-mark check-met">1</span>
                <span>Send your admission question to the ZYNTRA WhatsApp number.</span>
              </li>
              <li>
                <span className="check-mark check-met">2</span>
                <span>The assistant searches approved SZABIST admission sources.</span>
              </li>
              <li>
                <span className="check-mark check-met">3</span>
                <span>You receive a guidance answer. Confirm final details with SZABIST.</span>
              </li>
            </ol>
            <p className="field-hint" style={{ marginTop: 14 }}>
              Do not send passwords, verification codes or payment details over WhatsApp.
            </p>
          </section>
        </div>
      )}
    </>
  )
}

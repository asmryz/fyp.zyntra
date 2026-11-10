import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useOutletContext } from 'react-router-dom'
import HeroLogo from '../../components/landing/HeroLogo'
import { Alert, EmptyState, RichText, Skeleton } from '../../components/ui/Feedback'
import Icon from '../../components/ui/Icon'
import { useApi } from '../../hooks/useApi'
import { usePageTitle } from '../../hooks/usePageTitle'

// What the platform does. This describes ZYNTRA itself, so it lives in the
// frontend; SZABIST information comes from the database.
const OFFERS = [
  {
    id: 'admission-guidance',
    title: 'Admission Guidance',
    text: 'Admission requirements, program details and general guidance from approved sources, organised in one place instead of scattered across many.',
    link: '/programs',
    linkLabel: 'Explore programs',
  },
  {
    id: 'test-preparation',
    title: 'AI-Powered Test Preparation',
    text: 'Study topic explanations, curated videos, learning resources and past papers for the admission test. AI-supported explanations are being integrated.',
    link: '/student/test-prep',
  },
  {
    id: 'career-roadmaps',
    title: 'Program and Career Roadmaps',
    text: 'Follow connected roadmaps from foundation subjects to skills, specialisations, tools and the job roles they lead to.',
    link: '/student/roadmaps',
  },
  {
    id: 'scholarships',
    title: 'Scholarship Guidance',
    text: 'Understand scholarship types, eligibility, benefits, required documents and the application process, step by step.',
    link: '/student/scholarships',
  },
  {
    id: 'whatsapp',
    title: 'WhatsApp Admission Assistance',
    text: 'Ask admission questions from WhatsApp once the ZYNTRA assistant is connected, using the same approved sources.',
    link: '/student/whatsapp',
  },
]

const STEPS = [
  { title: 'Create your account', text: 'Register with your email and confirm it with a one-time code.' },
  { title: 'Build your profile', text: 'Add your qualification, marks and the program you are interested in.' },
  { title: 'Review program criteria', text: 'Compare your background with each program’s published admission criteria.' },
  { title: 'Prepare and plan', text: 'Prepare for the admission test, explore roadmaps and review scholarships.' },
]

// Program cards shown on the landing page (two rows of four on desktop)
const PROGRAM_PREVIEW_COUNT = 8

const MARQUEE_ITEMS = ['Admission Guidance', 'Test Preparation', 'Career Roadmaps', 'Scholarships', 'WhatsApp Assistance']

/** Scroll to #section links, including when arriving from another page. */
function useScrollToHash() {
  const { hash } = useLocation()
  useEffect(() => {
    if (!hash) return
    const target = document.getElementById(hash.slice(1))
    target?.scrollIntoView({ block: 'start' })
  }, [hash])
}

/** Returns the id of the offer row closest to the middle of the screen. */
function useActiveRow(ids) {
  const [activeId, setActiveId] = useState(ids[0])
  const refs = useRef({})

  useEffect(() => {
    if (!('IntersectionObserver' in window)) return undefined
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => entry.isIntersecting && setActiveId(entry.target.id))
      },
      { rootMargin: '-45% 0px -45% 0px' },
    )
    Object.values(refs.current).forEach((element) => element && observer.observe(element))
    return () => observer.disconnect()
  }, [])

  return [activeId, refs]
}

function ContentBlock({ block, loading, fallbackTitle }) {
  if (loading) {
    return (
      <div style={{ display: 'grid', gap: 10 }}>
        <Skeleton height={26} width="40%" />
        <Skeleton height={16} />
        <Skeleton height={16} width="85%" />
      </div>
    )
  }
  return (
    <div className="about-block">
      <h3>{block?.title || fallbackTitle}</h3>
      {block ? <RichText text={block.body} /> : <p>This information will be published soon.</p>}
    </div>
  )
}

export default function LandingPage() {
  usePageTitle(null)
  useScrollToHash()
  const { siteContent } = useOutletContext()
  const programs = useApi('/api/public/programs')
  const [activeOffer, offerRefs] = useActiveRow(OFFERS.map((offer) => offer.id))
  const content = siteContent.data || {}

  return (
    <div className="landing">
      {/* ---------- Hero ---------- */}
      <section className="hero" aria-labelledby="hero-title">
        <div className="container hero-inner">
          <p className="eyebrow hero-eyebrow">AI-powered admission assistance for SZABIST</p>
          <HeroLogo />
          <div className="hero-bottom">
            <h1 id="hero-title" className="hero-title">
              Your Journey to SZABIST Starts&nbsp;Here.
            </h1>
            <div className="hero-side">
              <p className="hero-text">
                Explore programs, understand admission requirements, prepare for admission tests, discover
                scholarships, and plan your future with ZYNTRA.
              </p>
              <div className="hero-actions">
                <a href="#offers" className="btn btn-primary">
                  Explore ZYNTRA
                </a>
                <Link to="/register" className="btn btn-secondary">
                  Create Student Account
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="marquee" aria-hidden="true">
        <div className="marquee-track">
          {[...MARQUEE_ITEMS, ...MARQUEE_ITEMS].map((item, index) => (
            <span key={index} className="marquee-item">
              {item}
            </span>
          ))}
        </div>
      </div>

      {/* ---------- About SZABIST ---------- */}
      <section id="about" className="section section-deep" aria-labelledby="about-title">
        <div className="container about-grid">
          <div>
            <p className="eyebrow eyebrow-warm">About SZABIST</p>
            <h2 id="about-title" className="section-title">
              {content.about_szabist?.title || 'About SZABIST'}
            </h2>
            {siteContent.loading ? (
              <div style={{ display: 'grid', gap: 10 }}>
                <Skeleton height={18} />
                <Skeleton height={18} width="80%" />
              </div>
            ) : (
              <RichText
                className="about-lead"
                text={content.about_szabist?.body || 'Information about SZABIST will be published soon.'}
              />
            )}
          </div>
          <div className="about-side">
            <ContentBlock block={content.why_zyntra} loading={siteContent.loading} fallbackTitle="Why ZYNTRA exists" />
            <div className="about-block">
              <h3>How ZYNTRA helps you decide</h3>
              <p>
                Check what each program requires, compare it with your own academic profile, and prepare with the
                right material before you apply through SZABIST’s official admission process.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- What ZYNTRA offers ---------- */}
      <section id="offers" className="section" aria-labelledby="offers-title">
        <div className="container offers-grid">
          <div className="offers-intro">
            <p className="eyebrow">What ZYNTRA offers</p>
            <h2 id="offers-title" className="section-title">
              Six ways to move from questions to a clear plan.
            </h2>
            <p>
              Every feature works from information approved by the ZYNTRA team, and every result is guidance to help
              you prepare, not an official decision.
            </p>
            <Link to="/register" className="btn btn-primary">
              Create Student Account
            </Link>
          </div>

          <ol className="offers-list">
            {OFFERS.map((offer, index) => (
              <li
                key={offer.id}
                id={offer.id}
                ref={(element) => {
                  offerRefs.current[offer.id] = element
                }}
                className={`offer-row ${activeOffer === offer.id ? 'is-active' : ''}`}
              >
                <span className="offer-number" aria-hidden="true">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <div>
                  <h3 className="offer-title">{offer.title}</h3>
                  <p>{offer.text}</p>
                  <Link to={offer.link} className="offer-link">
                    {offer.linkLabel || 'Open in your dashboard'} <Icon name="arrow-right" size={16} />
                  </Link>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ---------- How it works ---------- */}
      <section className="section section-navy-2" aria-labelledby="steps-title">
        <div className="container">
          <p className="eyebrow eyebrow-on-blue">How it works</p>
          <h2 id="steps-title" className="section-title">
            From first question to application-ready.
          </h2>
          <ol className="steps">
            {STEPS.map((step, index) => (
              <li key={step.title} className="step">
                <span className="step-number">Step {index + 1}</span>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ---------- Programs ---------- */}
      <section id="programs" className="section" aria-labelledby="programs-title">
        <div className="container">
          <div className="section-head">
            <div>
              <p className="eyebrow">Programs</p>
              <h2 id="programs-title" className="section-title">
                Explore SZABIST programs.
              </h2>
            </div>
            <Link to="/programs" className="btn btn-secondary">
              View all programs
            </Link>
          </div>

          {programs.loading && (
            <div className="program-chips">
              <Skeleton height={64} />
              <Skeleton height={64} />
              <Skeleton height={64} />
            </div>
          )}
          {programs.error && <Alert type="error">{programs.error.message}</Alert>}
          {programs.data?.length === 0 && (
            <EmptyState title="Programs are being prepared">
              Program information will appear here once it has been published by the ZYNTRA team.
            </EmptyState>
          )}
          {/* A short preview: the program name only. "View all programs" opens the full list. */}
          {programs.data?.length > 0 && (
            <ul className="program-chips">
              {programs.data.slice(0, PROGRAM_PREVIEW_COUNT).map((program) => (
                <li key={program.id}>
                  <Link to={`/programs/${program.slug}`} className="program-chip">
                    {program.name}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {/* ---------- Call to action ---------- */}
      <section className="section section-orange cta" aria-labelledby="cta-title">
        <div className="container cta-inner">
          <h2 id="cta-title" className="cta-title">
            Plan your SZABIST application with clarity.
          </h2>
          <div className="hero-actions">
            <Link to="/register" className="btn btn-navy">
              Create Student Account
            </Link>
            <Link to="/login" className="btn btn-outline-navy">
              Login
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

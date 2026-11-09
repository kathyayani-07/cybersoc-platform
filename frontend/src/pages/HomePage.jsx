import { Link } from 'react-router-dom';

const features = [
  {
    icon: '01',
    title: 'Incident management',
    description: 'Capture, assign and track security incidents through a clear, accountable response workflow.',
  },
  {
    icon: '02',
    title: 'Local Demo AI analysis',
    description: 'Use rule-driven analysis to classify suspicious activity and surface indicators and response guidance.',
  },
  {
    icon: '03',
    title: 'Operational visibility',
    description: 'Bring incident trends, alerts and reporting together in one analyst-focused workspace.',
  },
  {
    icon: '04',
    title: 'Audit-ready activity',
    description: 'Keep an append-only record of important actions to support investigation and accountability.',
  },
];

const workflow = [
  ['01', 'Detect', 'Bring a reported event or alert into the response workflow.'],
  ['02', 'Investigate', 'Review evidence, assign an analyst and record findings.'],
  ['03', 'Respond', 'Coordinate containment and resolution with human oversight.'],
];

function ShieldIcon() {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true" focusable="false">
      <path d="M24 4 40 10v12c0 10.1-6.7 17.8-16 22C14.7 39.8 8 32.1 8 22V10l16-6Z" />
      <path d="m17 24 5 5 10-11" />
    </svg>
  );
}

export default function HomePage() {
  return (
    <div className="landing-page">
      <header className="landing-header">
        <a className="landing-brand" href="#home" aria-label="CyberSOC home">
          <span className="landing-brand-mark"><ShieldIcon /></span>
          <span>
            <strong>CyberSOC</strong>
            <small>INCIDENT RESPONSE</small>
          </span>
        </a>
        <nav className="landing-nav" aria-label="Main navigation">
          <a className="landing-nav-active" href="#home">Home</a>
          <a href="#about">About</a>
          <a href="#features">Features</a>
          <Link className="landing-login" to="/login">Login <span aria-hidden="true">↗</span></Link>
        </nav>
      </header>

      <main>
        <section className="landing-hero" id="home">
          <div className="landing-hero-copy">
            <div className="landing-kicker"><span /> SECURITY OPERATIONS, CONNECTED</div>
            <h1>Respond to threats<br />with <span>clarity and control.</span></h1>
            <p className="landing-lead">
              A unified incident response workspace that helps security teams turn alerts into organized,
              actionable investigations.
            </p>
            <div className="landing-actions">
              <Link className="landing-primary-cta" to="/login">Get started <span aria-hidden="true">→</span></Link>
              <a className="landing-secondary-cta" href="#features">Explore the platform</a>
            </div>
            <div className="landing-assurance">
              <span className="landing-assurance-icon"><ShieldIcon /></span>
              <span><strong>Analyst-led by design</strong><small>AI-assisted insights. Human-owned decisions.</small></span>
            </div>
          </div>

          <div className="landing-hero-visual" aria-label="Cybersecurity incident response workflow illustration">
            <div className="landing-orbit landing-orbit-one" />
            <div className="landing-orbit landing-orbit-two" />
            <div className="landing-glow" />
            <div className="landing-console">
              <div className="landing-console-top">
                <div className="landing-window-dots"><i /><i /><i /></div>
                <span>RESPONSE WORKSPACE</span>
                <span className="landing-console-status"><i /> READY</span>
              </div>
              <div className="landing-console-body">
                <div className="landing-console-heading">
                  <span className="landing-console-shield"><ShieldIcon /></span>
                  <span><small>INCIDENT RESPONSE</small><strong>From signal to resolution</strong></span>
                </div>
                <div className="landing-flow">
                  {workflow.map(([number, title, description], index) => (
                    <div className="landing-flow-step" key={title}>
                      <span className="landing-step-number">{number}</span>
                      <span className="landing-step-copy"><strong>{title}</strong><small>{description}</small></span>
                      {index < workflow.length - 1 && <span className="landing-step-connector" aria-hidden="true" />}
                    </div>
                  ))}
                </div>
                <div className="landing-console-footer">
                  <span><i /> SECURE WORKSPACE</span>
                  <span>HUMAN OVERSIGHT ENABLED</span>
                </div>
              </div>
            </div>
            <div className="landing-float-card landing-float-top"><span className="landing-float-icon">↗</span><span><strong>Clear ownership</strong><small>Assigned response workflow</small></span></div>
            <div className="landing-float-card landing-float-bottom"><span className="landing-float-icon landing-float-blue">✓</span><span><strong>Evidence to action</strong><small>One connected view</small></span></div>
          </div>
        </section>

        <section className="landing-about" id="about">
          <div className="landing-section-heading">
            <p className="landing-kicker">BUILT FOR THE RESPONSE CYCLE</p>
            <h2>Make every security event<br /><span>easier to act on.</span></h2>
          </div>
          <div className="landing-about-copy">
            <p>
              CyberSOC brings incident handling, investigation context and operational visibility into one
              practical platform. It is designed to help teams coordinate work without losing sight of the
              evidence or the people responsible for decisions.
            </p>
            <p>
              Local rule-based analysis can support triage, while analysts retain control over assignments,
              containment and resolution.
            </p>
            <Link to="/login" className="landing-text-link">Enter the response workspace <span aria-hidden="true">→</span></Link>
          </div>
        </section>

        <section className="landing-features" id="features">
          <div className="landing-features-heading">
            <div>
              <p className="landing-kicker">ONE PLATFORM. A CLEARER RESPONSE.</p>
              <h2>Everything your team needs<br />to move with confidence.</h2>
            </div>
            <p className="landing-features-intro">
              Purposeful tools for the day-to-day work of detecting, investigating and responding to incidents.
            </p>
          </div>
          <div className="landing-feature-grid">
            {features.map((feature) => (
              <article className="landing-feature-card" key={feature.title}>
                <span className="landing-feature-icon">{feature.icon}</span>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
                <span className="landing-card-arrow" aria-hidden="true">↗</span>
              </article>
            ))}
          </div>
        </section>

        <section className="landing-objectives">
          <div className="landing-objective-mark"><ShieldIcon /></div>
          <div>
            <p className="landing-kicker">THE OBJECTIVE</p>
            <h2>Less fragmentation.<br /><span>More informed response.</span></h2>
          </div>
          <p>
            Give security teams a consistent place to organize incidents, share investigation context and
            maintain visibility from initial report through resolution.
          </p>
          <Link to="/login" className="landing-primary-cta">Open CyberSOC <span aria-hidden="true">→</span></Link>
        </section>
      </main>

      <footer className="landing-footer">
        <a className="landing-brand" href="#home" aria-label="CyberSOC home">
          <span className="landing-brand-mark"><ShieldIcon /></span>
          <span><strong>CyberSOC</strong><small>INCIDENT RESPONSE</small></span>
        </a>
        <p>AI-assisted incident response. Analyst-led outcomes.</p>
        <span>© {new Date().getFullYear()} CyberSOC Platform</span>
      </footer>
    </div>
  );
}

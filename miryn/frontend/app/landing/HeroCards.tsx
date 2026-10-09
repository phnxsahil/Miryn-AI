function ChatCard() {
  return (
    <article className="hero-card hero-card--chat" aria-hidden="true">
      <div className="hero-card__topline"><span className="hero-avatar" /><span>Miryn</span><span className="hero-card__time">09:42</span></div>
      <p className="hero-card__bubble">Hey! How was your day? <span aria-hidden="true">✦</span></p>
      <div className="hero-skeleton"><span /><span /><span className="hero-skeleton__short" /></div>
      <div className="hero-card__input"><span>Tell me what is on your mind...</span><b>↗</b></div>
    </article>
  );
}

function ThoughtCard() {
  return (
    <article className="hero-card hero-card--thought" aria-hidden="true">
      <p className="hero-card__eyebrow">A gentle way to reflect</p>
      {['Spot the Thought', 'Find the Distortion', 'Balance Your Thinking'].map((step, index) => (
        <div className="thought-step" key={step}>
          <span className="thought-step__number">0{index + 1}</span>
          <span>{step}</span>
          {index < 2 && <i />}
        </div>
      ))}
    </article>
  );
}

function FocusCard() {
  return (
    <article className="hero-card hero-card--focus" aria-hidden="true">
      <p className="hero-card__eyebrow">Make room for what matters</p>
      <div className="focus-grid">
        {['Stress & Anxiety Relief', 'Emotional Growth', 'Focus & Productivity', 'Sleep & Relaxation', 'Emotional Healing', 'Daily Mindfulness'].map((item) => <span key={item}><b>✦</b>{item}</span>)}
      </div>
    </article>
  );
}

function MoodPreviewCard() {
  return (
    <article className="hero-card hero-card--mood" aria-hidden="true">
      <p className="hero-card__eyebrow">Today, in context</p>
      <div className="hero-mood-stack">
        <MoodCard mood={moodItems[0]} compact />
        <MoodCard mood={moodItems[1]} compact />
      </div>
    </article>
  );
}

export default function HeroCards() {
  return (
    <div className="hero-cards" aria-hidden="true">
      <ChatCard />
      <ThoughtCard />
      <FocusCard />
      <MoodPreviewCard />
    </div>
  );
}
import MoodCard, { moodItems } from "./MoodCard";

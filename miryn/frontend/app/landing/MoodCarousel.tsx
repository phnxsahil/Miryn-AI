import MoodCard, { moodItems } from "./MoodCard";
import Reveal from "./Reveal";

export default function MoodCarousel() {
  return (
    <Reveal ambient className="mood-carousel" role="region" tabIndex={0} aria-label="Mood context examples">
      {moodItems.map((mood) => <MoodCard key={mood.title} mood={mood} />)}
    </Reveal>
  );
}

import MoodCard, { moodItems } from "./MoodCard";

export default function MoodCarousel() {
  return (
    <div className="mood-carousel" aria-label="Mood context examples">
      {moodItems.map((mood) => <MoodCard key={mood.title} mood={mood} />)}
    </div>
  );
}

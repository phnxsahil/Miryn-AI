import PersonaDetailView from "@/components/Compare/PersonaDetailView";

export default function PersonaDetailPage({
  params,
}: {
  params: { userId: string };
}) {
  return <PersonaDetailView userId={params.userId} />;
}

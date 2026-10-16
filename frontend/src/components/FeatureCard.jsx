/**
 * FeatureCard — Reusable card component for feature/benefit display.
 */
export default function FeatureCard({ icon: Icon, title, description, badge }) {
  return (
    <div className="group relative rounded-2xl border border-[#3a3838] bg-gradient-to-b from-[#2a2929] to-[#242323] p-6 transition-all duration-300 hover:border-[#FF8900]/40 hover:shadow-lg hover:shadow-[#FF8900]/5">
      {/* Top accent line on hover */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-[#FF8900]/0 to-transparent group-hover:via-[#FF8900]/60 transition-all duration-500 rounded-t-2xl" />

      <div className="flex items-start justify-between mb-4">
        <div className="p-2.5 rounded-xl bg-[#1c1b1b] border border-[#383636] text-[#FF8900] group-hover:bg-[#FF8900]/10 group-hover:border-[#FF8900]/30 transition-colors duration-300">
          <Icon className="w-5 h-5" />
        </div>
        {badge && (
          <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-[#FF8900]/10 text-[#FF8900] border border-[#FF8900]/25 tracking-wider">
            {badge}
          </span>
        )}
      </div>

      <h3 className="text-base font-semibold text-white tracking-tight mb-2">{title}</h3>
      <p className="text-sm text-[#a8a3a3] leading-relaxed">{description}</p>
    </div>
  )
}

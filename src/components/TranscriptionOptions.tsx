export default function TranscriptionOptions() {
  const options = [
    {
      id: 'lyrics',
      icon: '🎤',
      title: 'Transcribe Lyrics',
      description: 'AI-powered lyric transcription',
      color: 'from-blue-500 to-blue-600',
      available: true,
    },
    {
      id: 'chords',
      icon: '🎸',
      title: 'Transcribe Chords',
      description: 'Detect chord progressions',
      color: 'from-purple-500 to-purple-600',
      available: true,
    },
    {
      id: 'transpose',
      icon: '🔄',
      title: 'Transpose',
      description: 'Change key signature',
      color: 'from-orange-500 to-orange-600',
      available: false,
    },
    {
      id: 'nashville',
      icon: '🔢',
      title: 'Nashville Numbers',
      description: 'Convert to number system',
      color: 'from-green-500 to-green-600',
      available: false,
    },
  ];

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-blue-200">
      <h2 className="text-xl font-semibold text-[#3f3f3f] mb-4">Transcription Options</h2>

      <div className="grid grid-cols-2 gap-3">
        {options.map((option) => (
          <button
            key={option.id}
            disabled={!option.available}
            className={`p-4 rounded-xl text-left transition-all ${
              option.available
                ? `bg-gradient-to-br ${option.color} text-white hover:shadow-lg hover:scale-105`
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            <div className="text-3xl mb-2">{option.icon}</div>
            <div className="font-semibold mb-1">{option.title}</div>
            <div className="text-xs opacity-90">{option.description}</div>
            {!option.available && (
              <div className="mt-2">
                <span className="px-2 py-1 bg-yellow-400 text-yellow-900 text-xs rounded-full font-semibold">
                  Coming Soon
                </span>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

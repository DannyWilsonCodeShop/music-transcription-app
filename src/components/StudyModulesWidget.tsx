export default function StudyModulesWidget() {
  return (
    <div className="bg-white rounded-xl shadow-md p-4 border border-blue-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-[#3f3f3f] flex items-center gap-2">
          🎓 Study Modules
        </h3>
      </div>

      <div className="space-y-3">
        <div className="p-4 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border border-blue-100 hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-2xl flex-shrink-0">
              🎓
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-[#3f3f3f] mb-1">
                Nashville Number System
              </h4>
              <p className="text-xs text-gray-600 mb-2">
                Learn the professional chord notation system used by session musicians worldwide.
              </p>
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                  12 Lessons
                </span>
                <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full font-medium">
                  Beginner
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 bg-gradient-to-br from-orange-50 to-yellow-50 rounded-lg border border-orange-100 hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-yellow-500 rounded-lg flex items-center justify-center text-2xl flex-shrink-0">
              🎸
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-[#3f3f3f] mb-1">
                Chord Theory Basics
              </h4>
              <p className="text-xs text-gray-600 mb-2">
                Master the fundamentals of chord construction and progressions.
              </p>
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-full font-medium">
                  8 Lessons
                </span>
                <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full font-medium">
                  Beginner
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 bg-gradient-to-br from-green-50 to-teal-50 rounded-lg border border-green-100 hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-teal-500 rounded-lg flex items-center justify-center text-2xl flex-shrink-0">
              🎹
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-[#3f3f3f] mb-1">
                Ear Training
              </h4>
              <p className="text-xs text-gray-600 mb-2">
                Develop your ability to identify chords and intervals by ear.
              </p>
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                  15 Lessons
                </span>
                <span className="px-2 py-1 bg-teal-100 text-teal-700 text-xs rounded-full font-medium">
                  Intermediate
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

#include "perfetto.h"

#include <chrono>
#include <fstream>
#include <iostream>
#include <thread>

PERFETTO_DEFINE_CATEGORIES(
    perfetto::Category("skill_demo").SetDescription("Skill integration probe"));
PERFETTO_TRACK_EVENT_STATIC_STORAGE();

int main(int argc, char** argv) {
  if (argc != 2) {
    std::cerr << "Usage: " << argv[0] << " OUTPUT.pftrace\n";
    return 2;
  }
  std::ofstream output(argv[1], std::ios::binary | std::ios::trunc);
  if (!output) {
    std::cerr << "Cannot open trace output: " << argv[1] << '\n';
    return 1;
  }
  perfetto::TracingInitArgs init;
  init.backends = perfetto::kInProcessBackend;
  perfetto::Tracing::Initialize(init);
  perfetto::TrackEvent::Register();

  perfetto::TraceConfig config;
  config.add_buffers()->set_size_kb(1024);
  auto* source = config.add_data_sources()->mutable_config();
  source->set_name("track_event");
  perfetto::protos::gen::TrackEventConfig categories;
  categories.add_disabled_categories("*");
  categories.add_enabled_categories("skill_demo");
  source->set_track_event_config_raw(categories.SerializeAsString());
  auto session = perfetto::Tracing::NewTrace();
  session->Setup(config);
  session->StartBlocking();

  auto process_track = perfetto::ProcessTrack::Current();
  auto descriptor = process_track.Serialize();
  descriptor.mutable_process()->set_process_name("SkillPerfettoDemo");
  perfetto::TrackEvent::SetTrackDescriptor(process_track, descriptor);
  {
    TRACE_EVENT("skill_demo", "SkillWork");
    TRACE_COUNTER("skill_demo", "QueueDepth", 3);
    {
      TRACE_EVENT("skill_demo", "Parse", "items", 3);
      std::this_thread::sleep_for(std::chrono::milliseconds(2));
    }
    {
      TRACE_EVENT("skill_demo", "Render");
      std::this_thread::sleep_for(std::chrono::milliseconds(2));
    }
    TRACE_COUNTER("skill_demo", "QueueDepth", 0);
  }  // End every scoped event before flushing/stopping.
  perfetto::TrackEvent::Flush();
  session->StopBlocking();
  auto bytes = session->ReadTraceBlocking();
  if (bytes.empty()) {
    std::cerr << "Tracing session produced no trace bytes\n";
    return 1;
  }
  output.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
  output.close();
  if (!output) {
    std::cerr << "Failed writing trace: " << argv[1] << '\n';
    return 1;
  }
  std::cout << "Trace written: " << argv[1] << '\n';
  return 0;
}

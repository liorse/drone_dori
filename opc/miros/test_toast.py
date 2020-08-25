import re
from miros import stripped

def trace_through_all_states():
  oven = ToasterOvenMock(name="oven")
  oven.start_at(door_closed)
  # Open the door
  oven.post_fifo(Event(signal=signals.Door_Open))
  # Close the door
  oven.post_fifo(Event(signal=signals.Door_Close))
  # Bake something
  oven.post_fifo(Event(signal=signals.Baking))
  # Open the door
  oven.post_fifo(Event(signal=signals.Door_Open))
  # Close the door
  oven.post_fifo(Event(signal=signals.Door_Close))
  # Toast something
  oven.post_fifo(Event(signal=signals.Toasting))
  # Open the door
  oven.post_fifo(Event(signal=signals.Door_Open))
  # Close the door
  oven.post_fifo(Event(signal=signals.Door_Close))
  time.sleep(0.01)
  return oven.trace()

def spy_on_light_on():
  oven = ToasterOvenMock(name="oven")
  oven.start_at(door_closed)
  # Open the door to turn on the light
  oven.post_fifo(Event(signal=signals.Door_Open))
  time.sleep(0.01)
  # turn our array into a paragraph
  return "\n".join(oven.spy())

def spy_on_light_off():
  oven = ToasterOvenMock(name="oven")
  # The light should be turned off when we start
  oven.start_at(door_closed)
  time.sleep(0.01)
  # turn our array into a paragraph
  return "\n".join(oven.spy())

def spy_on_buzz():
  oven = ToasterOvenMock(name="oven")
  oven.start_at(door_closed)
  # Send the buzz event
  oven.post_fifo(Event(signal=signals.Buzz))
  time.sleep(0.01)
  # turn our array into a paragraph
  return "\n".join(oven.spy())

def spy_on_heater_on():
  oven = ToasterOvenMock(name="oven")
  # The light should be turned off when we start
  oven.start_at(door_closed)
  oven.post_fifo(Event(signal=signals.Toasting))
  time.sleep(0.02)
  # turn our array into a paragraph
  return "\n".join(oven.spy())

def spy_on_heater_off():
  oven = ToasterOvenMock(name="oven")
  # The light should be turned off when we start
  oven.start_at(door_closed)
  oven.post_fifo(Event(signal=signals.Toasting))
  oven.clear_spy()
  oven.post_fifo(Event(signal=signals.Off))
  time.sleep(0.01)
  # turn our array into a paragraph
  return "\n".join(oven.spy())

def test_buzz_timing():
  # Test in the range of ms so we don't have to wait around for results
  toast_time, bake_time = 0.1, 0.2
  get_ready_sec = 0.01
  done_buzz_period_sec = 0.03

  oven = ToasterOvenMock(
    name="oven",
    toast_time_in_sec=toast_time,
    bake_time_in_sec=bake_time,
    get_ready_sec=get_ready_sec,
    done_buzz_period_sec=done_buzz_period_sec)

  # start our oven in the door_closed state
  oven.start_at(door_closed)

  # Buzz timing testing specifications and helper functions
  TS = namedtuple('TargetAndToleranceSpec', ['desc', 'offset', 'tolerance'])

  def make_test_spec(cook_time_sec, get_ready_sec, done_buzz_period_sec, tolerance_in_ms=3):
    "create as specification where define everything in ms"
    ts = [
      TS(desc="get ready buzz",
        offset=1000*(cook_time_sec-get_ready_sec),
        tolerance=tolerance_in_ms),
      TS(desc="first done buzz" ,
        offset=1000*(cook_time_sec),
        tolerance=tolerance_in_ms),
      TS(desc="second done buzz",
        offset=1000*(cook_time_sec+done_buzz_period_sec),
        tolerance=tolerance_in_ms)]
    return ts

  def test_buzz_events(test_type, start_time, spec, buzz_times):
    for (desc, offset, tolerance), buzz_time in zip(spec, buzz_times):

      # only keep track of ms, allow for wrapping of time
      bottom_bound = (start_time+offset-tolerance) % 1000
      top_bound = (start_time+offset+tolerance) % 1000

      # allow for wrapping of time
      if bottom_bound > top_bound:
        bottom_bound -= 1000
      try:
        assert(bottom_bound <= float(buzz_time) <= top_bound)
      except:
        # if you land here try increasing your tolerance
        print("FAILED: testing {} {}".format(test_type, desc))
        print("{} <= {} <= {}".format(bottom_bound, buzz_time, top_bound))

  toasting_buzz_test_spec = make_test_spec(toast_time, get_ready_sec, done_buzz_period_sec)

  # Toast something
  oven.post_fifo(Event(signal=signals.Toasting))
  time.sleep(1)
  trace_line = ToasterOvenMock.instrumentation_line_of_match(oven.trace(), "Toasting")
  toasting_time_ms = int(ToasterOvenMock.get_100ms_from_timestamp(trace_line))
  buzz_times = [int(ToasterOvenMock.get_100ms_from_timestamp(line)) for
                line in re.findall(r'\[.+\] buzz', "\n".join(oven.spy()))]
  test_buzz_events('toasting', toasting_time_ms, toasting_buzz_test_spec, buzz_times)

  # clear the spy and trace logs for another test
  oven.clear_spy()
  oven.clear_trace()

  baking_buzz_test_spec = make_test_spec(bake_time, get_ready_sec, done_buzz_period_sec)

  # Bake something
  oven.post_fifo(Event(signal=signals.Baking))
  time.sleep(1)
  oven.post_fifo(Event(signal=signals.Baking))
  trace_line = ToasterOvenMock.instrumentation_line_of_match(oven.trace(), "Baking")
  baking_time_ms = int(ToasterOvenMock.get_100ms_from_timestamp(trace_line))
  buzz_times = [int(ToasterOvenMock.get_100ms_from_timestamp(line)) for
                line in re.findall(r'\[.+\] buzz', "\n".join(oven.spy()))]
  test_buzz_events('baking', baking_time_ms, baking_buzz_test_spec, buzz_times)

# Confirm our graph's structure
trace_target = """
[2019-02-04 06:37:04.538413] [oven] e->start_at() top->off
[2019-02-04 06:37:04.540290] [oven] e->Door_Open() off->door_open
[2019-02-04 06:37:04.540534] [oven] e->Door_Close() door_open->off
[2019-02-04 06:37:04.540825] [oven] e->Baking() off->baking
[2019-02-04 06:37:04.541109] [oven] e->Door_Open() baking->door_open
[2019-02-04 06:37:04.541393] [oven] e->Door_Close() door_open->baking
[2019-02-04 06:37:04.541751] [oven] e->Toasting() baking->toasting
[2019-02-04 06:37:04.542083] [oven] e->Door_Open() toasting->door_open
[2019-02-04 06:37:04.542346] [oven] e->Door_Close() door_open->toasting
"""

with stripped(trace_target) as stripped_target, \
     stripped(trace_through_all_states()) as stripped_trace_result:

  for target, result in zip(stripped_target, stripped_trace_result):
    assert(target == result)

# Confirm the our statemachine is triggering the methods we want when we want them
assert re.search(r'light_off', spy_on_light_off())

# Confirm our light turns on
assert re.search(r'light_on', spy_on_light_on())

# Confirm the heater turns on
assert re.search(r'heater_on', spy_on_heater_on())

# Confirm the heater turns off
assert re.search(r'heater_off', spy_on_heater_off())

# Confirm our buzzer works
assert re.search(r'buzz', spy_on_buzz())

# Confirm the buzzer timing features are working
test_buzz_timing()

# Ride Share: Brazil - Cab Simulator

An immersive, accessible **audiogame** simulating the life of a taxi/ride-sharing driver in Brazil, featuring real-time motor sound synthesis and multiple classic cars (Chevette, Corsa, Gol).

Developed with native support for screen readers (**NVDA** and **SAPI5**) to ensure 100% accessibility for blind and visually impaired players.

---

## 🎮 Game Controls

### 🚗 Vehicle & Driving
- **L**: Turn engine ON / OFF (Key ignition - hold to start, tap accelerating `W` for a cold start!)
- **P**: Open/Close smartphone (Uber App)
- **Space**: Confirm actions on the smartphone app (Go online, accept ride, CNH registration)
- **F**: Query Voice GPS (Speaks the current distance and cardeal direction of the destination)
- **W / S / A / D** or **Arrow Keys**: Steer and drive the car (or walk on foot outside the car)
- **Up / Down Arrows (when in car)**: Change Automatic Gearbox mode (**P**ark, **R**everse, **N**eutral, **D**rive)
- **1, 2, 3, 4, 5**: Read dashboard telemetry (Motor status, current gear/mode, speed, RPM, engine temperature)
- **Escape**: Shut down the motor and return to the main menu

### 🔊 Audio Navigation (3D Sound GPS)
While on a trip, the GPS will emit **stereo panning beeps** to guide you:
- **Left Ear Beep**: Turn/Head Left.
- **Right Ear Beep**: Turn/Head Right.
- **Center Beep**: Route is aligned (Keep going straight).

---

## ⚙️ How Save Data Works
Your progress (credits, driver profile, purchased cars) is saved automatically in the system's AppData directory to avoid loss when updating or running compiled executables:
- **Windows**: `%APPDATA%/RideShareBrazil/progresso.ini`
- **Linux/macOS**: `~/.config/RideShareBrazil/progresso.ini`

---

## 🛠️ Running Locally

### Prerequisites
Make sure you have Python 3.10+ installed. Install the dependencies:
```bash
pip install -r requirements.txt
```

Run the game:
```bash
python main.py
```

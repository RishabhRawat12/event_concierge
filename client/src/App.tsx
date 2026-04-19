import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AttendeeView from './pages/AttendeeView';
import StaffView from './pages/StaffView';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<AttendeeView />} />
        <Route path="/staff" element={<StaffView />} />
        <Route path="*" element={<AttendeeView />} />
      </Routes>
    </Router>
  );
}

export default App;

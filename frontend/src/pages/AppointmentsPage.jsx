import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Plus, Trash2, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { appointmentsAPI } from '../services/api';
import { Card, Badge, LoadingSpinner, EmptyState } from '../components/UI';

function BookingModal({ onClose, onBooked }) {
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    customer_name: '', customer_email: '', appointment_date: '',
    appointment_time: '', purpose: 'Product Demo',
  });
  const [booking, setBooking] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    appointmentsAPI.availableSlots()
      .then(r => { setSlots(r.data.slots); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    setBooking(true);
    try {
      await appointmentsAPI.create(form);
      onBooked();
      onClose();
    } catch (e) {
      setError(e.message);
      setBooking(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Book Appointment</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
        </div>

        <form onSubmit={submit} className="p-6 space-y-4">
          <input required placeholder="Customer Name" value={form.customer_name}
            onChange={e => set('customer_name', e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300" />
          <input required type="email" placeholder="Email" value={form.customer_email}
            onChange={e => set('customer_email', e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300" />

          {/* Available slots */}
          <div>
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2 block">Select Time Slot</label>
            {loading ? <LoadingSpinner size="sm" /> : (
              <div className="space-y-3">
                {slots.map((daySlot) => (
                  <div key={daySlot.date}>
                    <p className="text-xs font-medium text-gray-500 mb-1.5">{daySlot.day}</p>
                    <div className="flex flex-wrap gap-2">
                      {daySlot.available_slots.map((time) => (
                        <button
                          key={time} type="button"
                          onClick={() => { set('appointment_date', daySlot.date); set('appointment_time', time); }}
                          className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
                            form.appointment_date === daySlot.date && form.appointment_time === time
                              ? 'bg-indigo-600 border-indigo-600 text-white'
                              : 'border-gray-200 text-gray-600 hover:border-indigo-300'
                          }`}
                        >
                          {time}
                        </button>
                      ))}
                      {daySlot.available_slots.length === 0 && (
                        <span className="text-xs text-gray-400">Fully booked</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <input placeholder="Purpose (e.g. Product Demo)" value={form.purpose}
            onChange={e => set('purpose', e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300" />

          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
              <AlertCircle size={14} /> {error}
            </div>
          )}

          <button type="submit"
            disabled={booking || !form.customer_name || !form.customer_email || !form.appointment_date}
            className="w-full py-3 bg-indigo-600 text-white rounded-xl font-medium text-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {booking ? 'Booking...' : 'Confirm Appointment'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const load = async () => {
    try {
      const res = await appointmentsAPI.list();
      setAppointments(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const cancel = async (id) => {
    if (!confirm('Cancel this appointment?')) return;
    try {
      await appointmentsAPI.cancel(id);
      load();
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
          <p className="text-sm text-gray-500 mt-1">Manage product demos and meetings</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          <Plus size={16} /> New Appointment
        </button>
      </div>

      <Card>
        {loading ? (
          <div className="flex justify-center py-16"><LoadingSpinner size="lg" /></div>
        ) : appointments.length === 0 ? (
          <EmptyState
            icon={Calendar}
            title="No appointments yet"
            description="Book a product demo or meeting. The AI agent can book appointments automatically during conversations."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100">
                  {['Customer', 'Email', 'Date', 'Time', 'Purpose', 'Status', 'Actions'].map(h => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {appointments.map((appt) => (
                  <tr key={appt.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-800 text-sm">{appt.customer_name}</td>
                    <td className="px-6 py-4 text-gray-500 text-sm">{appt.customer_email}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <Calendar size={12} className="text-gray-400" />
                        {appt.appointment_date}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <Clock size={12} className="text-gray-400" />
                        {appt.appointment_time}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{appt.purpose}</td>
                    <td className="px-6 py-4"><Badge label={appt.status} /></td>
                    <td className="px-6 py-4">
                      {appt.status !== 'cancelled' && (
                        <button onClick={() => cancel(appt.id)}
                          className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                          <Trash2 size={14} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {showModal && <BookingModal onClose={() => setShowModal(false)} onBooked={load} />}
    </div>
  );
}

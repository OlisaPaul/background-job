import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Form, Button, Card, Spinner, Alert, Row, Col } from "react-bootstrap";
import API_BASE from "../api/config";
import "./FormStyles.css";

const scheduleTypes = [
  { value: "immediate", label: "Immediate" },
  { value: "scheduled", label: "Scheduled" },
  { value: "interval", label: "Interval" },
];

const frequencies = [
  { value: "once", label: "Once" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

export default function EditJobForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [form, setForm] = useState({
    schedule_type: "",
    scheduled_time: "",
    frequency: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/jobs/${id}/`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch job");
        return res.json();
      })
      .then((data) => {
        setJob(data);
        setForm({
          schedule_type: data.schedule_type || "",
          scheduled_time: data.scheduled_time
            ? data.scheduled_time.slice(0, 16)
            : "",
          frequency: data.frequency || "",
        });
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [id]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setSubmitError(null);
    const patchData = {
      schedule_type: form.schedule_type,
      scheduled_time: form.scheduled_time
        ? new Date(form.scheduled_time).toISOString()
        : null,
      frequency: form.frequency,
    };
    try {
      const res = await fetch(`${API_BASE}/jobs/${id}/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patchData),
      });
      if (!res.ok) throw new Error("Failed to update job");
      navigate("/");
    } catch (e) {
      setSubmitError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading)
    return (
      <div
        className="d-flex justify-content-center align-items-center"
        style={{ height: "60vh" }}
      >
        <Spinner animation="border" />
      </div>
    );
  if (error) return <Alert variant="danger">{error}</Alert>;
  if (!job) return null;

  // Only allow editing if job is pending or scheduled/interval
  const canEdit =
    job.status === "pending" ||
    ["scheduled", "interval"].includes(job.schedule_type);

  return (
    <Row
      className="justify-content-center align-items-center"
      style={{ minHeight: "80vh" }}
    >
      <Col xs={12} md={8} lg={6}>
        <Card className="p-4 shadow">
          <Card.Title>Edit Job #{job.id}</Card.Title>
          {!canEdit && (
            <Alert variant="warning">This job cannot be edited.</Alert>
          )}
          <Form onSubmit={handleSubmit} className="mt-3">
            <Form.Group className="mb-3">
              <Form.Label>Schedule Type</Form.Label>
              <Form.Select
                name="schedule_type"
                value={form.schedule_type}
                onChange={handleChange}
                disabled={!canEdit}
                required
              >
                <option value="">Select schedule type</option>
                {scheduleTypes.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
            {(form.schedule_type === "scheduled" ||
              form.schedule_type === "interval") && (
              <Form.Group className="mb-3">
                <Form.Label>Scheduled Time</Form.Label>
                <Form.Control
                  type="datetime-local"
                  name="scheduled_time"
                  value={form.scheduled_time}
                  onChange={handleChange}
                  disabled={!canEdit}
                  required={form.schedule_type !== "immediate"}
                />
              </Form.Group>
            )}
            {form.schedule_type === "interval" && (
              <Form.Group className="mb-3">
                <Form.Label>Frequency</Form.Label>
                <Form.Select
                  name="frequency"
                  value={form.frequency}
                  onChange={handleChange}
                  disabled={!canEdit}
                  required
                >
                  <option value="">Select frequency</option>
                  {frequencies.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            )}
            <div className="d-flex justify-content-between align-items-center mt-4">
              <Button
                variant="secondary"
                onClick={() => navigate(-1)}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={!canEdit || submitting}
              >
                {submitting ? (
                  <Spinner size="sm" animation="border" />
                ) : (
                  "Save Changes"
                )}
              </Button>
            </div>
            {submitError && (
              <Alert variant="danger" className="mt-3">
                {submitError}
              </Alert>
            )}
          </Form>
        </Card>
      </Col>
    </Row>
  );
}

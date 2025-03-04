import React from 'react'
import { Container, Pagination, Card, Col, Row, Button, Modal, Table, Spinner, Form, InputGroup, OverlayTrigger, Tooltip } from 'react-bootstrap'
import { useParams, useNavigate } from 'react-router-dom'
import { useMQTTControl, useMQTTState } from './MQTTContext';
import dayjs from 'dayjs'
import { useToastDispatch, add_toast } from "./ToastContext";

import { useMachineList, useMachineReasons, useMachineStatus, useMachineStoppages, useSetReason } from './api'

export function LivePage({ }) {
  let { data: machine_list, isLoading } = useMachineList()
  const { sendJsonMessage, subscribe, unsubscribe } = useMQTTControl()
  let params = useParams();
  let navigate = useNavigate()
  const machine_id = params.machine_id

  let [subscribed, setSubscribed] = React.useState(false)
  let [current_event, setCurrentEvent] = React.useState(undefined)

  let toast_dispatch = useToastDispatch()


  React.useEffect(() => {
    if (!subscribed) {
      subscribe("downtime/state/" + machine_id + "/#")
      setSubscribed(true)
    }
  }, [machine_id, subscribe, subscribed])

  React.useEffect(() => {
    return () => {
      unsubscribe("downtime/state/" + machine_id + "/#")
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])


  if (isLoading) {
    return <Container fluid="md">
      <Card className='mt-2 text-center'>
        <Spinner></Spinner>
      </Card>
    </Container>
  }



  let machine = machine_list.find(elem => elem.id === machine_id)

  const manualSetStatus = async (value) => {
    let topic = "downtime/event/" + machine_id + "/" + (value ? "start" : "stop")
    let payload = { machine: machine_id, running: value, source: "user" }
    try {
      sendJsonMessage(topic, payload, 1);
      add_toast(toast_dispatch, { header: "Sent" })
    }
    catch (err) {
      console.error(err)
      add_toast(toast_dispatch, { header: "Error", body: err })
    }
  }


  return <SelectReasonModalWrapper event={current_event} setEvent={setCurrentEvent} machine_id={machine_id}>
    <Card className='mt-0'>
      <Card.Header className='text-center'>
        <h1 className='d-flex'>
          <span>Downtime - {machine?.name}</span>
          <OverlayTrigger overlay={<Tooltip>Go to View / Edit Event History page</Tooltip>}>
            <button className='bi bi-journal-bookmark icon_button ms-auto' onClick={() => navigate("/history/" + machine_id)} />
          </OverlayTrigger>
        </h1>
      </Card.Header>
      <Card.Body>
        <StatusBar machine_id={machine_id} manualSetStatus={manualSetStatus} />
        <EventLog machine_id={machine_id} handleEventClick={(event) => setCurrentEvent(event)} />
      </Card.Body>
    </Card>
  </SelectReasonModalWrapper>
}

export function SelectReasonModalWrapper({ children, machine_id, event, setEvent }) {
  let [selected_category, setSelectedCategory] = React.useState(undefined)

  let set_reason = useSetReason(machine_id)

  const handleReasonClick = (reason_id) => {
    set_reason.mutate({ record_id: event.record_id, reason: reason_id })
    setEvent(undefined)
    setSelectedCategory(undefined)
  }

  const closeModal = () => {
    setEvent(undefined);
    setSelectedCategory(undefined)
  }

  return <>
    {children}
    <ReasonModal
      machine_id={machine_id}
      show={event !== undefined}
      handleReasonClick={handleReasonClick}
      selected_category={selected_category}
      handleCategoryClick={(id) => setSelectedCategory(id)}
      close={closeModal} />
  </>
}

function EventLog({ machine_id, handleEventClick }) {
  const [page, setPage] = React.useState(1)
  const page_length = 10
  const [duration_filter, setDurationFilter] = React.useState("")

  let { data: stoppages, isLoading } = useMachineStoppages(machine_id, page, page_length, duration_filter)


  if (isLoading) {
    return <div>Loading...</div>
  }

  let duration_filter_elements = [5, 10, 15, 20, 30, 45, 60].map(step => (<option value={step} key={step}>{step} min</option>))

  return <Card className='mt-3 mx-2'>

    <div className="d-flex justify-content-between align-items-baseline">
      <Pagination size="sm" className="my-1 mx-1">
        <Pagination.Item
          onClick={() => setPage(1)}
          disabled={page <= 1}
        >
          Back to Latest
        </Pagination.Item>
        <Pagination.Item
          onClick={() => setPage(prev => prev - 1)}
          disabled={page <= 1}
        >
          Newer
        </Pagination.Item>
        <Pagination.Item
          onClick={() => setPage(prev => prev + 1)}
          disabled={stoppages.length < page_length}
        >
          Older
        </Pagination.Item>
      </Pagination>
      <div>Page {page}</div>
      <div className="my-1 mx-1">
        <OverlayTrigger overlay={<Tooltip>Minimum duration - only shows stops that last longer than this.</Tooltip>}>
          <InputGroup>
            <InputGroup.Text>Minimum Duration</InputGroup.Text>
            <Form.Select value={duration_filter} onChange={(evt) => setDurationFilter(evt.target.value)}>
              <option value={""}>None</option>
              {duration_filter_elements}
            </Form.Select>
          </InputGroup>
        </OverlayTrigger>
      </div>
    </div>
    <Table bordered striped responsive="sm" className='mb-2'>
      <thead>
        <tr>
          <th>Start</th>
          <th>End</th>
          <th>Duration</th>
          <th>Reason</th>
        </tr>
      </thead>
      <tbody>
        {stoppages.map((event, index) => (<tr key={index}>
          <RenderTimestampCell timestamp={event.start} />
          <RenderTimestampCell timestamp={event.end} />
          <RenderDurationCell event={event} />
          <RenderReasonButtonCell machine_id={machine_id} event={event} handleEventClick={handleEventClick} />
        </tr>
        ))}
        {stoppages.length < page_length && <tr><td colSpan={4} className='text-center'>End of Records</td></tr>}
      </tbody>
    </Table>
  </Card>
}


export function RenderTimestampCell({ timestamp }) {
  let rendered_timestamp = "-"
  if (timestamp) {
    let timestamp_obj = dayjs(timestamp)
    if (timestamp_obj.isToday())
      rendered_timestamp = timestamp_obj.format('HH:mm:ss')
    else
      rendered_timestamp = timestamp_obj.format('DD/MM/YYYY HH:mm:ss')
  }
  return <td>{rendered_timestamp}</td>
}

export function RenderDurationCell({ event }) {
  const [_, setBumpState] = React.useState(true);

  let duration = ""
  let refresh = undefined
  if (event?.end) {
    duration = <div>{format_duration(dayjs.duration(dayjs(event.end).diff(dayjs(event.start))))}</div>
  } else {
    let duration_value = dayjs.duration(dayjs().diff(dayjs(event.start)))
    duration = <div> {format_duration(duration_value)}<i className='blink'>.</i></div>
    refresh = (duration_value >= dayjs.duration(1, 'minutes')) ? 59000 : 900
  }

  React.useEffect(() => {
    if (refresh !== undefined) {
      const interval = setInterval(() => setBumpState(prev => !prev), refresh);
      return () => {
        clearInterval(interval);
      };
    }
  }, [refresh]);

  return <td>{duration}</td >
}

function format_duration(d) {
  if (d >= dayjs.duration(1, 'days'))
    return d.format('D[d] H[h] m[m]')
  else if (d >= dayjs.duration(1, 'hours'))
    return d.format('H[h] m[m]')
  else if (d >= dayjs.duration(1, 'minutes'))
    return d.format('m[m]')
  else
    return d.format('s[s]')
}

export function RenderReasonButtonCell({ machine_id, event, handleEventClick }) {

  let { data: reason_set, isLoading } = useMachineReasons(machine_id)

  if (isLoading) {
    return <td><Spinner /></td>
  }

  let final_cell_content = <Button variant="outline-primary" onClick={() => handleEventClick(event)}>Set Reason</Button>
  let final_cell_classes = 'd-grid h-100 p-1'
  if (event.reason) { //if reason set
    let reason_entry = reason_set.reasons[event.reason]
    let category_entry = reason_set.categories[reason_entry.category]
    final_cell_content = <Button style={{ backgroundColor: category_entry.colour, borderColor: 'transparent', color: 'black' }} onClick={() => handleEventClick(event)}>{category_entry.category_name + " - " + reason_entry.text}</Button>
    final_cell_classes = 'd-grid p-1'
  }

  return <td className={final_cell_classes}>{final_cell_content}</td>
}

function StatusBar({ machine_id, manualSetStatus }) {
  let { data: status } = useMachineStatus(machine_id)
  let { data: machine_list } = useMachineList()
  let machine = machine_list.find(machine => machine.id === machine_id)

  let status_bar = <Button variant="secondary" size="lg" disabled={true}>Status: Disconnected</Button>
  let button = ""
  if (status?.running === true) {
    status_bar = <Button variant="success" size="lg" disabled={true}>Status: Running</Button>
    button = <Button variant="outline-danger" size="lg" onClick={() => manualSetStatus(false)}>Stop</Button>
  } else if ((status?.running === false) || (machine?.enable_manual_input === true && status === undefined)) {
    status_bar = <Button variant="danger" size="lg" disabled={true}>Status: Stopped</Button>
    button = <Button variant="outline-success" size="lg" onClick={() => manualSetStatus(true)}>Start</Button>
  }


  if (machine?.enable_manual_input === true)
    return <Container fluid>
      <Row className='gx-2 gy-1'>
        <Col xs={12} md={8} className="d-grid px-1">
          {status_bar}
        </Col>
        <Col xs={12} md={4} className="d-grid px-1">
          {button}
        </Col>
      </Row>
    </Container>
  else
    return <Container fluid>
      <Row className='gx-2 gy-1'>
        <Col xs={12} className="d-grid px-1">
          {status_bar}
        </Col>
      </Row>
    </Container>
}

function ReasonModal({ machine_id, show, handleReasonClick, selected_category, handleCategoryClick, close }) {

  let { data: reason_set, isLoading } = useMachineReasons(machine_id)

  if (isLoading) {
    return <Modal show={show} fullscreen={true}>
      <Spinner></Spinner>
    </Modal>
  }

  let category_modal = <> <Modal.Header className='text-center'>
    <Modal.Title className="w-100 d-flex flex-row justify-content-between">
      <Button variant='light' onClick={() => handleReasonClick(null)}>Set to "No Reason"</Button>
      <h2>Reason Categories</h2>
      <Button variant='light' onClick={() => close()}>Close</Button>
    </Modal.Title>
  </Modal.Header>
    <Modal.Body>
      <Row className='gx-2 gy-2'>
        {Object.keys(reason_set.categories).map(category_id => (
          <Col xs={12} sm={6} md={4} lg={3} key={category_id} className='d-grid'>
            <Button style={{ backgroundColor: reason_set.categories[category_id].colour, borderColor: 'transparent', color: 'black' }} size='lg' onClick={() => handleCategoryClick(category_id)}>
              {reason_set.categories[category_id].category_name}
            </Button>
          </Col>
        ))}
      </Row>
    </Modal.Body>
  </>

  let chosen_category = reason_set.categories[selected_category]

  let reason_modal = <>
    <Modal.Header className='text-center'>
      <Modal.Title className="w-100">Reason for Category {chosen_category?.category_name} <Button variant='light' className='float-end' onClick={() => handleCategoryClick(undefined)}>Back</Button></Modal.Title>
    </Modal.Header>
    <Modal.Body>
      <Row className='gx-2 gy-2'>
        {chosen_category?.reasons.map(reason_id => (
          <Col xs={12} sm={6} md={4} lg={3} key={reason_id} className='d-grid'>
            <Button variant="primary" size='lg' onClick={() => handleReasonClick(reason_id)}>
              {reason_set.reasons[reason_id].text}
            </Button>
          </Col>
        ))}
      </Row>
    </Modal.Body>
  </>


  return <Modal show={show} fullscreen={true}>
    {selected_category === undefined ? category_modal : reason_modal}
  </Modal>
}

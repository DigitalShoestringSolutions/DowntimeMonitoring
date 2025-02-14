import React from 'react'
import { Container, Pagination, Card, Col, Row, Button, Modal, Table, Spinner } from 'react-bootstrap'
import { useParams } from 'react-router-dom'
import { useMQTTControl, useMQTTState } from './MQTTContext';
import dayjs from 'dayjs'
import { useToastDispatch, add_toast } from "./ToastContext";

import { STATUS } from './variables';
import { useConfig, useMachineList, useMachineReasons, useMachineStatus, useMachineStoppages, useSetReason } from './api'

export function LivePage({ }) {

  let { data: config } = useConfig()
  let { data: machine_list, isLoading } = useMachineList(config)
  const { sendJsonMessage, subscribe, unsubscribe } = useMQTTControl()
  let params = useParams();
  const machine_id = params.machine_id
  let { data: reason_set } = useMachineReasons(config, machine_id)


  let [showModal, setShowModal] = React.useState(false);
  let [subscribed, setSubscribed] = React.useState(false)
  let [selected_category, setSelectedCategory] = React.useState(undefined)
  let [current_event, setCurrentEvent] = React.useState(undefined)

  let toast_dispatch = useToastDispatch()
  let set_reason = useSetReason(config, machine_id)


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
    let topic = "downtime/event/"+machine_id+"/"+(value?"start":"stop")
    let payload = { machine: machine_id, running: value, source: "user" }
    try {
      sendJsonMessage(topic, payload);
      add_toast(toast_dispatch, { header: "Sent" })
    }
    catch (err) {
      console.error(err)
      add_toast(toast_dispatch, { header: "Error", body: err })
    }
  }

  const handleEventClick = (event) => {
    setShowModal(true)
    setCurrentEvent(event)
  }

  const handleReasonClick = (reason_id) => {
    setShowModal(false)
    set_reason.mutate({ record_id: current_event.record_id, reason: reason_id })
    setSelectedCategory(undefined)
    setCurrentEvent(undefined)
  }

  const closeModal = () => {
    setShowModal(false);
    setSelectedCategory(undefined)
    setCurrentEvent(undefined)
  }

  return <>
    <Card className='mt-0'>
      <Card.Header className='text-center'>
        <h1>{machine?.name}</h1>
      </Card.Header>
      <Card.Body>
        <StatusBar machine_id={machine_id} config={config} manualSetStatus={manualSetStatus}/>
        <EventLog machine_id={machine_id} config={config} handleEventClick={handleEventClick} reason_set={reason_set} />
      </Card.Body>
    </Card>
    <ReasonModal
      show={showModal}
      handleReasonClick={handleReasonClick}
      selected_category={selected_category}
      handleCategoryClick={(id) => setSelectedCategory(id)}
      reason_set={reason_set}
      close={closeModal} />
  </>
}

function EventLog({ machine_id, config, handleEventClick, reason_set }) {
  const [page, setPage] = React.useState(1)
  const page_length = 10
  let { data: stoppages, isLoading } = useMachineStoppages(config, machine_id, page, page_length)

  if (isLoading) {
    return <div>Loading...</div>
  }

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
      <div className="my-1 mx-2" />
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
        {stoppages.map((event, index) => {
          // timestamp formatting
          let start_timestamp = "-"
          if (event.start) {
            let start_time_obj = dayjs(event.start)
            if (start_time_obj.isToday())
              start_timestamp = start_time_obj.format('HH:mm:ss')
            else
              start_timestamp = start_time_obj.format('DD/MM/YYYY HH:mm:ss')
          }


          let end_timestamp = "-"
          if (event?.end) {
            let end_time_obj = dayjs(event.end)
            if (end_time_obj.isToday())
              end_timestamp = end_time_obj.format('HH:mm:ss')
            else
              end_timestamp = end_time_obj.format('DD/MM/YYYY HH:mm:ss')
          }

          // format final cell
          let final_cell_content = <Button variant="outline-primary" onClick={() => handleEventClick(event)}>Set Reason</Button>
          let final_cell_classes = 'd-grid h-100 p-1 text-center'
          if (event.reason) { //if reason set
            let reason_entry = reason_set.reasons[event.reason]
            let category_entry = reason_set.categories[reason_entry.category]
            final_cell_content = <Button style={{ backgroundColor: category_entry.colour, borderColor: 'transparent', color: 'black' }} onClick={() => handleEventClick(event)}>{category_entry.category_name + " - " + reason_entry.text}</Button>
            final_cell_classes = 'd-grid p-1 text-center'
          }

          return <tr key={index}>
            <td>{start_timestamp}</td>
            <td>{end_timestamp}</td>
            <td>{event.end ? format_duration(dayjs.duration(dayjs(event.end).diff(dayjs(event.start)))) : ""}</td>
            <td className={final_cell_classes}>{final_cell_content}</td>
          </tr>
        })}
        {stoppages.length < page_length && <tr><td colSpan={4} className='text-center'>End of Records</td></tr>}
      </tbody>
    </Table>
  </Card>
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

function StatusBar({ config, machine_id, manualSetStatus }) {
  let { data: status } = useMachineStatus(config, machine_id)
  let { data: machine_list } = useMachineList(config)
  let machine = machine_list.find(machine => machine.id === machine_id)

  let status_bar = <Button variant="secondary" size="lg" disabled={true}>Status: Disconnected</Button>
  let button = ""
  if (status?.running === true) {
    status_bar = <Button variant="success" size="lg" disabled={true}>Status: Running</Button>
    button = <Button variant="outline-danger" size="lg" onClick={() => manualSetStatus(false)}>Stop</Button>
  } else if (status?.running === false) {
    status_bar = <Button variant="danger" size="lg" disabled={true}>Status: Stopped</Button>
    button = <Button variant="outline-success" size="lg" onClick={() => manualSetStatus(true)}>Start</Button>
  }

  return <Container fluid>
    <Row className='gx-2 gy-1'>
      <Col xs={12} md={8} className="d-grid px-1">
        {status_bar}
      </Col>
      <Col xs={12} md={4} className="d-grid px-1">
        {(machine?.sensor === false)
          ? button
          : ""}
      </Col>
    </Row>
  </Container>
}

function ReasonModal({ show, handleReasonClick, selected_category, handleCategoryClick, reason_set, close }) {

  let category_modal = <> <Modal.Header className='text-center'>
    <Modal.Title className="w-100">Reason Categories <Button variant='light' className='float-end' onClick={() => close()}>Close</Button></Modal.Title>
  </Modal.Header>
    <Modal.Body>
      <Row className='gx-2 gy-2'>
        {reason_set && Object.keys(reason_set.categories).map(category_id => (
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

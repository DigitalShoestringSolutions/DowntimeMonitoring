import React from 'react'
import { Container, Pagination, Card, Col, Row, Button, Modal, Table, Spinner, Form, InputGroup, OverlayTrigger, Tooltip, ButtonGroup, Alert } from 'react-bootstrap'
import { useParams, useNavigate } from 'react-router-dom'
import { useMQTTControl, useMQTTState } from './MQTTContext';
import dayjs from 'dayjs'
import { useToastDispatch, add_toast } from "./ToastContext";

import { useConfig, useMachineList, useEventList, useMachineReasons, useSetReason, useModifyEvent, useDeleteEvent } from './api'
import { RenderDurationCell, RenderReasonButtonCell, RenderTimestampCell, SelectReasonModalWrapper } from './DataCapturePage';

export function EventHistoryPage({ }) {
    let params = useParams();
    let navigate = useNavigate()
    const machine_id = params.machine_id

    let { data: config } = useConfig()
    let { data: machine_list, isLoading } = useMachineList(config)
    const { subscribe, unsubscribe } = useMQTTControl()
    let [subscribed, setSubscribed] = React.useState(false)

    let [current_event, setCurrentEvent] = React.useState(undefined)

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

    return <SelectReasonModalWrapper event={current_event} setEvent={setCurrentEvent} machine_id={machine_id}>
        <Card className='mt-0'>
            <Card.Header className='text-center'>
                <h1 className='d-flex'>
                    <span>History - {machine?.name}</span>
                    <OverlayTrigger overlay={<Tooltip>Go to Record Downtime page</Tooltip>}>
                        <button className='bi bi-stopwatch icon_button ms-auto' onClick={() => navigate("/downtime/" + machine_id)} />
                    </OverlayTrigger>
                </h1>
            </Card.Header>
            <Card.Body>
                <EventLog machine={machine} handleEventClick={(event) => setCurrentEvent(event)} />
            </Card.Body>
        </Card>
    </SelectReasonModalWrapper>
}


function EventLog({ machine, handleEventClick }) {
    let { data: config } = useConfig()
    const [page, setPage] = React.useState(1)
    const page_length = 10
    const [from, setFrom] = React.useState(dayjs().startOf("day"))
    const [to, setTo] = React.useState(dayjs().endOf("day"))

    let { data: event_list, isLoading } = useEventList(
        config,
        machine.id,
        page,
        page_length,
        from ? from.toISOString() : undefined,
        to ? to.toISOString() : undefined
    )
    let { data: reason_set, isLoading: reasons_loading } = useMachineReasons(config, machine.id)

    let [edit_modal, setEditModal] = React.useState(undefined)


    if (isLoading || reasons_loading) {
        return <div>Loading...</div>
    }

    let duration_filter_elements = [5, 10, 15, 20, 30, 45, 60].map(step => (<option value={step} key={step}>{step} min</option>))

    let edit = (event) => {
        setEditModal(event)
    }

    return <Card className='mt-0 mx-2'>
        <div className='mx-1 mt-1'>
            <InputGroup>
                <InputGroup.Text>Timeframe</InputGroup.Text>
                <InputGroup.Text>From</InputGroup.Text>
                <Form.Control type="date" value={from ? from.format("YYYY-MM-DD") : ""} onChange={(evt) => setFrom(dayjs(evt.target.value).startOf("day"))} />
                <OverlayTrigger overlay={<Tooltip>Clear "from" date</Tooltip>}>
                    <Button className='bi bi-x-lg' variant="outline-secondary" onClick={() => setFrom("")} />
                </OverlayTrigger>

                <InputGroup.Text>To</InputGroup.Text>
                <Form.Control type="date" value={to ? to.format("YYYY-MM-DD") : ""} onChange={(evt) => setTo(dayjs(evt.target.value).endOf("day")
                )} />
                <OverlayTrigger overlay={<Tooltip>Clear "to" date</Tooltip>}>
                    <Button className='bi bi-x-lg' variant="outline-secondary" onClick={() => setTo("")} />
                </OverlayTrigger>
            </InputGroup>
        </div>
        <div className="d-flex justify-content-between align-items-baseline">
            <Pagination size="sm" className="my-1 mx-1">
                <Pagination.Item
                    onClick={() => setPage(1)}
                    disabled={page <= 1}
                >
                    Back to Start
                </Pagination.Item>
                <Pagination.Item
                    onClick={() => setPage(prev => prev - 1)}
                    disabled={page <= 1}
                >
                    Back
                </Pagination.Item>
                <Pagination.Item
                    onClick={() => setPage(prev => prev + 1)}
                    disabled={event_list.length < page_length}
                >
                    Next
                </Pagination.Item>
            </Pagination>
            <div>Page {page}</div>
            <div className="my-1 mx-1">
            </div>
        </div>
        <Table bordered responsive="sm" className='mb-2'>
            <thead>
            </thead>
            <tbody>
                {event_list.map((event, state_index) => {

                    let output = []
                    output.push(<tr key={state_index} className={event.running ? 'table-success' : 'table-danger'}>
                        <RenderTimestampCell timestamp={event.start} />
                        <RenderTimestampCell timestamp={event.end} />
                        <RenderDurationCell event={event} />
                        {event.running === false ?
                            <RenderReasonButtonCell event={event} machine_id={machine.id} handleEventClick={handleEventClick} />
                            : <td className='text-center'>Running</td>}
                        <td></td>
                    </tr>)

                    output.push(...event?.events_during.map(
                        (event, index) => <RenderEventRow key={state_index + "_" + index} event={event} machine={machine} edit={edit} />
                    ))
                    output.push(<RenderEventRow key={state_index + "_trigger"} event={event.trigger_event} machine={machine} edit={edit} />)

                    return output
                })}
                {event_list.length < page_length && <tr><td colSpan={4} className='text-center'>End of Records</td></tr>}
            </tbody>
        </Table>
        <EditModal event={edit_modal} close={() => setEditModal(undefined)} />
    </Card>
}

function RenderRunningCell({ running }) {
    if (running) {
        return <td className='bi bi-arrow-return-right'> Start</td>
    } else {
        return <td className='bi bi-sign-stop-fill'> Stop</td>
    }
}

function RenderSourceCell({ source }) {
    let source_element = ""
    if (source == "sensor")
        source_element = <span className='bi bi-plug-fill'> Sensor</span>
    if (source == "user")
        source_element = <span className='bi bi-person-fill'> User</span>

    return <td>{source_element}</td>
}

function RenderEventRow({ event, machine, edit }) {

    let controls = ""
    if ((event?.source === "user" && machine?.edit_manual_input === true) || (event?.source === "sensor" && machine?.edit_sensor_input === true))
        controls = <Button size="sm" variant="outline-secondary" onClick={() => edit(event)}>Edit</Button>

    return <tr>
        <td></td>
        <RenderRunningCell running={event?.running} />
        <RenderSourceCell source={event?.source} />
        <RenderTimestampCell timestamp={event?.timestamp} />
        <td className='d-grid p-1'>{controls}</td>
    </tr>
}

function EditModal({ event, close }) {
    let [date, setDate] = React.useState(undefined)
    let [time, setTime] = React.useState(undefined)
    let [error, setError] = React.useState(undefined)

    let updateEvent = useModifyEvent()
    let deleteEvent = useDeleteEvent()

    React.useEffect(() => {
        let timestamp = dayjs(event?.timestamp)
        setDate(timestamp.format("YYYY-MM-DD"))
        setTime(timestamp.format("HH:mm:ss"))
        setError(undefined)
    }, [event])

    const do_update = () => {
        let new_timestamp = dayjs(date + " " + time)
        console.log(new_timestamp.toISOString())
        updateEvent.mutate({ event_id: event.event_id, timestamp: new_timestamp }, {
            onSuccess: (result, variables, context) => {
                close()
            },
            onError: (error, variables, context) => {
                setError(error?.payload)
            }
        })
    }

    const do_delete = () => {
        deleteEvent.mutate({ event_id: event.event_id }, {
            onSuccess: (result, variables, context) => {
                close()
            },
            onError: (error, variables, context) => {
                setError(error?.payload)
            }
        })
    }

    return <Modal show={event !== undefined} onHide={close} fullscreen={false}>
        <Modal.Header className='text-center' closeButton>
            <Modal.Title className="w-100">Edit {event?.running ? "Start" : "Stop"} Event</Modal.Title>
        </Modal.Header>
        <Modal.Body>
            <InputGroup>
                <InputGroup.Text>Date</InputGroup.Text>
                <Form.Control type="date" value={date} onChange={(evt) => setDate(evt.target.value)} />
                <InputGroup.Text>Time</InputGroup.Text>
                <Form.Control type="time" value={time} onChange={(evt) => setTime(evt.target.value)} />
            </InputGroup>
            {error?.error &&
                <Alert variant="danger">
                    <div>{error.reason}.</div>
                    {error?.limit &&
                        <div> Must be {error.error == "too_early" ? "after" : "before"} {dayjs(error.limit).format("YYYY-MM-DD HH:mm:ss")}.</div>
                    }
                </Alert>
            }
            <ButtonGroup className='mt-2 w-100'>
                <Button variant="danger" onClick={do_delete}>Delete Event</Button>
                <Button onClick={do_update}>Update Timestamp</Button>
            </ButtonGroup>
        </Modal.Body>
    </Modal>
}
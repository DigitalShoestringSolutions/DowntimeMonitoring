import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css'
import React from 'react'
import dayjs from 'dayjs'
import duration from 'dayjs/plugin/duration';
import isToday from 'dayjs/plugin/isToday'
import { BrowserRouter, Routes, Route, NavLink, Outlet } from 'react-router-dom'
import { Container, Navbar, Nav, Row, Col, ToastContainer, Toast, Card, Spinner, ListGroup, Button, ButtonGroup, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { MQTTProvider, useMQTTState } from './MQTTContext';
import { ToastProvider } from './ToastContext'
import { LivePage } from './DataCapturePage'
import { new_message_action, custom_reducer, initial_state } from './custom_mqtt';
import { useConfig, useMachineList } from './api'


import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import { EventHistoryPage } from './EventHistoryPage';

dayjs.extend(isToday);
dayjs.extend(duration);

// Create a client
const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MQTTWrapper>
        <ToastProvider position='bottom-end'>
          <BrowserRouter>
            <Routing />
          </BrowserRouter>
        </ToastProvider>
      </MQTTWrapper>
    </QueryClientProvider>
  )

}

function MQTTWrapper({ children }) {

  let { data: config, isLoading } = useConfig()


  if (isLoading) {
    return <Container fluid="md">
      <Card className='mt-2 text-center'>
        <div><Spinner></Spinner> <h2 className='d-inline'>Loading Config</h2></div>
      </Card>
    </Container>
  } else {

    return <MQTTProvider
      host={config?.mqtt?.host ?? window.location.hostname}
      port={config?.mqtt?.port ?? 9001}
      prefix={config?.mqtt?.prefix ?? []}
      new_message_action={new_message_action}
      reducer={custom_reducer}
      initial_state={initial_state}
    // debug={true}
    >
      {children}
    </MQTTProvider>
  }
}

function Routing({ }) {
  return (
    <Routes>
      <Route path='/' element={<Base />}>
        <Route path='/machines' element={<MachineList />} />
        {/* <Route path='/machine/m/:machine_id' element={<CapturePage machine_list={machine_list} {...props} />} /> */}
        <Route path='/downtime/:machine_id' element={<LivePage />} />
        <Route path="/history/:machine_id" element={<EventHistoryPage />} />
        <Route index element={<MachineList />}></Route>
      </Route>
    </Routes>
  )
}

function Base({ setMachineList }) {

  let { connected } = useMQTTState()
  let variant = "danger"
  let text = "Disconnected"
  if (connected) {
    variant = "success"
    text = "Connected"
  }



  return (
    <Container fluid className="vh-100 p-0 d-flex flex-column">
      {/* <div id='header'> */}
      <Navbar sticky="top" bg="secondary" variant="dark" expand="md">
        <Container fluid>
          <Navbar.Brand href="/">
            Shoestring Downtime Monitoring
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" className='mb-2' />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav variant="pills">
              <BSNavLink to='/machines'>Machine List</BSNavLink>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>
      {/* </div> */}
      <Container fluid className="flex-grow-1 main-background px-1 pt-2 px-sm-2">
        <Row className="h-100 m-0 d-flex justify-content-center pt-4 pb-1">
          <Col md={10} lg={8}>
            <Outlet />
          </Col>
        </Row>
      </Container>
      <div className='bottom_bar'>
        <ButtonGroup aria-label="Basic example">
          <OverlayTrigger
            placement='top'
            overlay={
              <Tooltip>
                Live updates over MQTT: {text}
              </Tooltip>
            }
          >
            <Button variant={variant} className='bi bi-rss'>{" " + text}</Button>
          </OverlayTrigger>
        </ButtonGroup>
      </div>
    </Container>
  )

}

function BSNavLink({ children, className, ...props }) {
  return <NavLink className={({ isActive }) => (isActive ? ("nav-link active " + className) : ("nav-link " + className))} {...props}>{children}</NavLink>
}

function MachineList({ url_prefix }) {

  let { data: machine_list, isLoading } = useMachineList()

  if (isLoading) {
    return <Container fluid="md">
      <Card className='mt-2 text-center'>
        <Spinner></Spinner>
      </Card>
    </Container>
  } else {
    return <Container fluid="md">
      <Card className='mt-2'>
        <Card.Header className='text-center'><h1>Machines</h1></Card.Header>
        <Card.Body>
          <ListGroup>
            {machine_list.map(item => (
              <ListGroup.Item key={item.id} className="d-flex justify-content-between align-items-baseline flex-wrap">
                <div className='flex-grow-1 flex-shrink-0'>
                  {item.name}
                </div>
                <span className='flex-shrink-1'>
                  <NavLink to={"/history/" + item.id}>
                    <Button className="m-1" variant="outline-secondary">View / Edit History</Button>
                  </NavLink>
                  <NavLink to={"/downtime/" + item.id}>
                    <Button className="m-1">Record Downtime</Button>
                  </NavLink>
                </span>
              </ListGroup.Item>
            ))}
          </ListGroup>
        </Card.Body>
      </Card>
    </Container>
  }
}

export default App;

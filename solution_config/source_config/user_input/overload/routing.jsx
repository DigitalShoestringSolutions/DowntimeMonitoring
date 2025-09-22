import { Routes, Route, NavLink, Outlet } from 'react-router-dom'
import { Container, Navbar, Nav, Row, Col, Card, Spinner, ListGroup, Button, ButtonGroup, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { useMQTTState } from 'core/context/mqtt';
import { LivePage } from 'app/DataCapturePage'
import { EventHistoryPage } from 'app/EventHistoryPage';
import { useMachineList } from 'app/api'


import 'app/index.css'

export function Routing() {
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


function Base({ }) {

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

function MachineList({ }) {

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

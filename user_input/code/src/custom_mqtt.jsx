
import { STATUS } from './variables';
import dayjs from 'dayjs'

export const initial_state = { events: {}, status: {}, status_updated: {} }

const uuid_regex = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
const new_state_entry_regex = new RegExp("downtime/state/" + uuid_regex + "/new")
const update_state_entry_regex = new RegExp("downtime/state/" + uuid_regex + "/update")
const remove_state_entry_regex = new RegExp("downtime/state/" + uuid_regex + "/remove")

export async function new_message_action(dispatch, queryClient, message) {
  console.log("MQTT>", message)
  if (message === undefined)
    return

  if (message.topic.match(new_state_entry_regex)) {
    let machine_id = message.payload.target
    // update status
    queryClient.setQueryData(['status', { id: machine_id }], (current_entry) => {
      let new_state_entry = message.payload
      if (current_entry == undefined || (new_state_entry?.start && dayjs(new_state_entry.start) > dayjs(current_entry.start)))
        return new_state_entry
      else
        return current_entry  //new entry is a historic insert
    })
    // invalidate event list if there is a new stoppage so it is re-fetched
    if (message.payload.running === false)
      queryClient.invalidateQueries({ queryKey: ['stoppages', { id: machine_id }], refetchType: 'active' })

  } else if (message.topic.match(update_state_entry_regex)) {
    let machine_id = message.payload.target

    // update record
    queryClient.setQueriesData({ queryKey: ['stoppages', { id: machine_id }], type: 'active' }, (old_data => {
      return old_data.map(entry => {
        if (entry.record_id === message.payload.record_id)  //replace if has matching record_id
          return message.payload
        else
          return entry
      })
    }))

    queryClient.invalidateQueries({ queryKey: ['events', { id: machine_id }], refetchType: 'active' })
  } else if (message.topic.match(remove_state_entry_regex)) {
    let machine_id = message.payload.target
    queryClient.invalidateQueries({ queryKey: ['stoppages', { id: machine_id }], refetchType: 'active' })
    queryClient.invalidateQueries({ queryKey: ['events', { id: machine_id }], refetchType: 'active' })
  }
}

export const custom_reducer = (currentState, action) => {
  // console.log(action,currentState)
  switch (action.type) {
    case 'MQTT_STATUS':
      return {
        ...currentState,
        connected: action.connected
      };
    default:
      throw new Error(`Unhandled action type: ${action.type}`);
  }
};

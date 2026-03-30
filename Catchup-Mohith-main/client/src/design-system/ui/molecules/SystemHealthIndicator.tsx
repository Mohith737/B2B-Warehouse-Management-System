// client/src/design-system/ui/molecules/SystemHealthIndicator.tsx
import { Grid, Column, Tag, Tile } from '@carbon/react'

type SystemHealthIndicatorProps = {
  databaseOk: boolean
  redisOk: boolean
  temporalOk: boolean
  lastTierRecalc: string | null
}

function serviceTag(isOk: boolean): JSX.Element {
  return <Tag type={isOk ? 'green' : 'red'}>{isOk ? 'Healthy' : 'Down'}</Tag>
}

export function SystemHealthIndicator({
  databaseOk,
  redisOk,
  temporalOk,
  lastTierRecalc,
}: SystemHealthIndicatorProps): JSX.Element {
  return (
    <Tile>
      <h4>System Health</h4>
      <Grid condensed>
        <Column lg={4} md={2} sm={4}>
          <p>Database</p>
          {serviceTag(databaseOk)}
        </Column>
        <Column lg={4} md={2} sm={4}>
          <p>Redis</p>
          {serviceTag(redisOk)}
        </Column>
        <Column lg={4} md={2} sm={4}>
          <p>Temporal</p>
          {serviceTag(temporalOk)}
        </Column>
      </Grid>
      <p>{`Last Tier Recalc: ${lastTierRecalc ?? 'Never'}`}</p>
    </Tile>
  )
}

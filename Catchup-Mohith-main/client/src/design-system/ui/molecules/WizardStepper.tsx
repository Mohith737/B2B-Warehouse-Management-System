// client/src/design-system/ui/molecules/WizardStepper.tsx
import { ProgressIndicator, ProgressStep } from '@carbon/react'

type WizardStepperProps = {
  steps: string[]
  currentStep: number
}

export function WizardStepper({ steps, currentStep }: WizardStepperProps): JSX.Element {
  return (
    <ProgressIndicator currentIndex={currentStep - 1} spaceEqually>
      {steps.map((step, index) => (
        <ProgressStep
          complete={index < currentStep - 1}
          current={index === currentStep - 1}
          description={step}
          key={step}
          label={step}
        />
      ))}
    </ProgressIndicator>
  )
}

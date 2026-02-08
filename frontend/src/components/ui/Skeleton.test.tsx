import { describe, it, expect } from 'vitest'
import { render } from '@/test/test-utils'
import {
  Skeleton,
  SkeletonText,
  SkeletonCircle,
  SkeletonCard,
  SkeletonStatCard,
  SkeletonTableRow,
  SkeletonTable,
  SkeletonListItem,
  SkeletonValidationItem,
  SkeletonDraftItem,
  SkeletonAnalyticsCard,
  SkeletonChart,
  SkeletonBatchJob,
} from './Skeleton'

describe('Skeleton', () => {
  it('renders with pulse animation class', () => {
    const { container } = render(<Skeleton />)
    expect(container.firstChild).toHaveClass('animate-pulse')
  })

  it('applies custom className', () => {
    const { container } = render(<Skeleton className="h-8 w-32" />)
    expect(container.firstChild).toHaveClass('h-8', 'w-32')
  })

  it('has rounded and background classes', () => {
    const { container } = render(<Skeleton />)
    expect(container.firstChild).toHaveClass('rounded-md', 'bg-gray-200')
  })
})

describe('SkeletonText', () => {
  it('renders single line by default', () => {
    const { container } = render(<SkeletonText />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons).toHaveLength(1)
  })

  it('renders multiple lines when specified', () => {
    const { container } = render(<SkeletonText lines={3} />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons).toHaveLength(3)
  })

  it('last line is shorter when multiple lines', () => {
    const { container } = render(<SkeletonText lines={3} />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons[2]).toHaveClass('w-3/4')
    expect(skeletons[0]).toHaveClass('w-full')
  })
})

describe('SkeletonCircle', () => {
  it('renders with default medium size', () => {
    const { container } = render(<SkeletonCircle />)
    expect(container.firstChild).toHaveClass('h-10', 'w-10', 'rounded-full')
  })

  it('renders small size', () => {
    const { container } = render(<SkeletonCircle size="sm" />)
    expect(container.firstChild).toHaveClass('h-8', 'w-8')
  })

  it('renders large size', () => {
    const { container } = render(<SkeletonCircle size="lg" />)
    expect(container.firstChild).toHaveClass('h-12', 'w-12')
  })
})

describe('SkeletonCard', () => {
  it('renders card structure with avatar and text', () => {
    const { container } = render(<SkeletonCard />)
    // Should have circle (avatar) and text skeletons
    expect(container.querySelector('.rounded-full')).toBeInTheDocument()
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(1)
  })

  it('applies custom className', () => {
    const { container } = render(<SkeletonCard className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})

describe('SkeletonStatCard', () => {
  it('renders stat card structure', () => {
    const { container } = render(<SkeletonStatCard />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons).toHaveLength(3) // label, value, subtext
  })
})

describe('SkeletonTableRow', () => {
  it('renders with default 4 columns', () => {
    const { container } = render(
      <table>
        <tbody>
          <SkeletonTableRow />
        </tbody>
      </table>
    )
    const cells = container.querySelectorAll('td')
    expect(cells).toHaveLength(4)
  })

  it('renders custom number of columns', () => {
    const { container } = render(
      <table>
        <tbody>
          <SkeletonTableRow columns={6} />
        </tbody>
      </table>
    )
    const cells = container.querySelectorAll('td')
    expect(cells).toHaveLength(6)
  })
})

describe('SkeletonTable', () => {
  it('renders with default rows and columns', () => {
    const { container } = render(<SkeletonTable />)
    const rows = container.querySelectorAll('tbody tr')
    expect(rows).toHaveLength(5) // default rows
  })

  it('renders custom rows and columns', () => {
    const { container } = render(<SkeletonTable rows={3} columns={5} />)
    const rows = container.querySelectorAll('tbody tr')
    const headerCells = container.querySelectorAll('thead th')
    expect(rows).toHaveLength(3)
    expect(headerCells).toHaveLength(5)
  })
})

describe('SkeletonListItem', () => {
  it('renders list item structure', () => {
    const { container } = render(<SkeletonListItem />)
    expect(container.querySelector('.rounded-full')).toBeInTheDocument()
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(2)
  })
})

describe('SkeletonValidationItem', () => {
  it('renders validation item structure', () => {
    const { container } = render(<SkeletonValidationItem />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(3)
  })
})

describe('SkeletonDraftItem', () => {
  it('renders draft item structure', () => {
    const { container } = render(<SkeletonDraftItem />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThanOrEqual(3)
  })

  it('applies custom className', () => {
    const { container } = render(<SkeletonDraftItem className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})

describe('SkeletonAnalyticsCard', () => {
  it('renders analytics card structure', () => {
    const { container } = render(<SkeletonAnalyticsCard />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThanOrEqual(3)
  })

  it('has card styling', () => {
    const { container } = render(<SkeletonAnalyticsCard />)
    expect(container.firstChild).toHaveClass('rounded-xl', 'border')
  })
})

describe('SkeletonChart', () => {
  it('renders chart placeholder with bars', () => {
    const { container } = render(<SkeletonChart />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    // Should have title skeleton + 12 bar skeletons
    expect(skeletons.length).toBeGreaterThanOrEqual(10)
  })

  it('has card styling', () => {
    const { container } = render(<SkeletonChart />)
    expect(container.firstChild).toHaveClass('rounded-xl', 'border')
  })
})

describe('SkeletonBatchJob', () => {
  it('renders batch job structure', () => {
    const { container } = render(<SkeletonBatchJob />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThanOrEqual(4)
  })

  it('has rounded border', () => {
    const { container } = render(<SkeletonBatchJob />)
    expect(container.firstChild).toHaveClass('rounded-lg', 'border')
  })
})
